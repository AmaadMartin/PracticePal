from fastapi import FastAPI, UploadFile, File, Request, HTTPException
import uvicorn
from exam_maker_agent import Agent
import tempfile
import shutil
from fastapi.middleware.cors import CORSMiddleware
import boto3
from AnswerChecker import isCorrectOpenEndedAnswer
import bcrypt
from fastapi.responses import JSONResponse
import stripe
import os
from dotenv import load_dotenv
import uuid
from mangum import Mangum
from google.oauth2 import id_token
from google.auth.transport import requests

load_dotenv()

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize AWS DynamoDB
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

dynamodb = session.resource("dynamodb", region_name="us-east-1")
# Main user table
user_table = dynamodb.Table("userbase")  # Ensure this table exists

# Temporary pending users table
pending_user_table = dynamodb.Table("pending_users")  # Create this table

# Pending tier changes table
pending_tier_changes_table = dynamodb.Table("pending_tier_changes")  # Create this table

credits_for_tier = {
    "free": 6,
    "gold": 15,
    "diamond": 50,
}


def create_user(
    email, password, tier, stripe_customer_id=None, is_google_account=False
):
    user_item = {
        "username": email,
        "stripe_customer_id": stripe_customer_id or "",
        "tier": tier,
        "exams": [],
        "exam_credits": credits_for_tier.get(tier, 0),
        "is_google_account": is_google_account,
    }
    if not is_google_account:
        user_item["password"] = password
    user_table.put_item(Item=user_item)


def create_checkout_session(email, tier, reference_id, is_change_tier=False, credits=0):
    # Map subscription tiers to Stripe Price IDs
    price_ids = {
        "free": os.getenv("STRIPE_FREE_PRICE"),
        "gold": os.getenv("STRIPE_GOLD_PRICE"),
        "diamond": os.getenv("STRIPE_DIAMOND_PRICE"),
    }
    if tier not in price_ids:
        raise ValueError("Invalid subscription tier: " + tier)

    # Set metadata to indicate whether it's a tier change
    metadata = {}
    if is_change_tier:
        metadata["change_tier"] = "true"
    else:
        metadata["signup"] = "true"

    if credits > 0:
        metadata["credits"] = str(credits)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_ids[tier],
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=f"{os.getenv('FRONTEND_URL')}/payment-success",
        cancel_url=f"{os.getenv('FRONTEND_URL')}/payment-cancel",
        customer_email=email,
        client_reference_id=reference_id,  # Pass the unique reference ID
        metadata=metadata,
    )
    return session


def create_credit_checkout_session(username, option):
    # Map credit options to Stripe Price IDs and number of credits
    credit_options = {
        "1_credit": {
            "price_id": os.getenv("STRIPE_PRICE_ID_1_CREDIT"),
            "credits": 1,
        },
        "10_credits": {
            "price_id": os.getenv("STRIPE_PRICE_ID_10_CREDITS"),
            "credits": 10,
        },
        "100_credits": {
            "price_id": os.getenv("STRIPE_PRICE_ID_100_CREDITS"),
            "credits": 100,
        },
    }
    if option not in credit_options:
        raise ValueError("Invalid credit option: " + option)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": credit_options[option]["price_id"],
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{os.getenv('FRONTEND_URL')}/payment-success",
        cancel_url=f"{os.getenv('FRONTEND_URL')}/payment-cancel",
        metadata={
            "username": username,
            "credits": str(credit_options[option]["credits"]),
        },
    )
    return session


test_questions = [
    {
        "question": "What is the capital of France?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital of France.",
    },
    {
        "question": "What is the capital of Germany?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Berlin",
        "explanation": "Berlin is the capital of Germany.",
    },
    {
        "question": "What is the capital of Spain?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Madrid",
        "explanation": "Madrid is the capital of Spain.",
    },
    {
        "question": "What is the capital of England?",
        "type": "oe",
        "correct_answer": "London",
        "explanation": "London is the capital of England.",
    },
]


def test_create_exam_response(user_id):
    response = user_table.get_item(Key={"username": user_id})
    item = response.get("Item")
    if item:
        exams = item.get("exams")
        exam_id = len(exams)
    else:
        exam_id = 0

    response = {
        "id": exam_id,
        "name": "Test Exam",
        "questions": test_questions,
        "message": "success",
    }
    user_table.update_item(
        Key={"username": user_id},
        UpdateExpression="SET exams = list_append(if_not_exists(exams, :empty_list), :response)",
        ExpressionAttributeValues={":empty_list": [], ":response": [response]},
    )
    return response


@app.post("/create_exam/{user_id}")
async def create_exam(files: list[UploadFile] = File(...), user_id: str = None):
    # get number of exams user has to get an id
    response = user_table.get_item(Key={"username": user_id})
    item = response.get("Item")
    if item:
        # check if user has atleast 1 exam credit or is not a free user to create an exam
        exam_credits = item.get("exam_credits")
        print("exam_credits", exam_credits)
        if exam_credits < 1:
            return {
                "message": "You do not have enough exam credits. They will reset next sunday."
            }

        # decrement exam credits
        user_table.update_item(
            Key={"username": user_id},
            UpdateExpression="SET exam_credits = exam_credits - :val",
            ExpressionAttributeValues={":val": 1},
        )

    if os.getenv("ENV") == "dev":
        return test_create_exam_response(user_id)

    # convert files to list of file objects while keeping their extensions
    files = [(file.filename, file.file) for file in files]
    threadId = agent.create_conversation(files)
    data = agent.run_agent(
        "Can you make a practice exam based on these class materials? Try to search as many files as possible for relevant information.",
        threadId,
    )
    agent.delete_thread(threadId)

    if item:
        exams = item.get("exams")
        exam_id = len(exams)
    else:
        exam_id = 0

    examName = data["exam_name"]
    questions = data["questions"]
    response = {
        "id": exam_id,
        "name": examName,
        "questions": questions,
        "message": "success",
    }

    # add response to database for user in exams field and decrement exam credits
    user_table.update_item(
        Key={"username": user_id},
        UpdateExpression="SET exams = list_append(if_not_exists(exams, :empty_list), :response)",
        ExpressionAttributeValues={
            ":empty_list": [],
            ":response": [response],
        },
    )
    return response


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    response = user_table.get_item(Key={"username": user_id})
    item = response.get("Item")
    if item:
        print(item)
        return item
    else:
        return {"message": "User not found"}


@app.post("/login")
async def login(data: dict):
    username = data["username"]
    username = username.lower()
    password = data["password"]

    # Fetch user from DynamoDB
    response = user_table.get_item(Key={"username": username})
    if "Item" not in response:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = response["Item"]
    stored_password_hash = user.get("password")

    # Verify password
    if not stored_password_hash or not bcrypt.checkpw(
        password.encode("utf-8"), stored_password_hash.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Login successful
    return {"message": "Login successful"}


@app.post("/signup")
async def signup(data: dict):
    # print(data)
    email = data["email"]
    email = email.lower()
    password = data["password"]
    tier = data["tier"]
    # print(email, password, tier)

    if not email or not password or not tier:
        raise HTTPException(
            status_code=400, detail="Email, password, and tier are required."
        )

    # Check if user already exists
    response = user_table.get_item(Key={"username": email})
    if "Item" in response:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Generate a unique user ID
    user_id = str(uuid.uuid4())

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

    if tier == "free":
        # Store user data in userbase table
        create_user(email, password_hash, tier)
        return {"free": True}

    # Store user data in pending_users table
    pending_user_table.put_item(
        Item={
            "user_id": user_id,
            "username": email,
            "password": password_hash,
            "tier": tier,
        }
    )

    try:
        # Create Checkout Session
        session = create_checkout_session(email, tier, user_id)
        return {"sessionId": session.id}
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        # Remove pending user data if session creation fails
        pending_user_table.delete_item(Key={"user_id": user_id})
        raise HTTPException(
            status_code=500, detail="Failed to create checkout session."
        )


@app.post("/google-login")
async def google_login(data: dict):
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        # Get user info
        email = idinfo["email"]

        # Check if user exists
        response = user_table.get_item(Key={"username": email})
        if "Item" not in response:
            # Create a new user
            create_user(email, "", "free", is_google_account=True)

        return {"username": email}
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=400, detail="Invalid token")


@app.post("/google-signup")
async def google_signup(data: dict):
    token = data.get("token")
    tier = data.get("tier")
    if not token or not tier:
        raise HTTPException(status_code=400, detail="Token and tier are required")

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        # Get user info
        email = idinfo["email"]

        # Check if user already exists
        response = user_table.get_item(Key={"username": email})
        if "Item" in response:
            raise HTTPException(status_code=400, detail="User already exists")

        # Generate a unique user ID
        user_id = str(uuid.uuid4())

        if tier == "free":
            # Create user immediately
            create_user(email, "", tier, is_google_account=True)
            return {"free": True}
        else:
            # Store user data in pending_users table
            pending_user_table.put_item(
                Item={
                    "user_id": user_id,
                    "username": email,
                    "tier": tier,
                    "is_google_account": True,
                }
            )
            # Create Checkout Session
            session = create_checkout_session(email, tier, user_id)
            return {"sessionId": session.id}
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        print(f"Error during Google signup: {e}")
        # Remove pending user data if session creation fails
        pending_user_table.delete_item(Key={"user_id": user_id})
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@app.post("/purchase_credits")
async def purchase_credits(data: dict):
    username = data.get("username")
    option = data.get("option")

    if not username or not option:
        raise HTTPException(status_code=400, detail="Username and option are required.")

    # Check if user exists
    response = user_table.get_item(Key={"username": username})
    if "Item" not in response:
        raise HTTPException(status_code=400, detail="User not found.")

    try:
        session = create_credit_checkout_session(username, option)
        return {"sessionId": session.id}
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create checkout session."
        )


@app.post("/change_tier")
async def change_tier(data: dict):
    username = data.get("username")
    new_tier = data.get("tier")

    if not username or not new_tier:
        raise HTTPException(
            status_code=400, detail="Username and new tier are required."
        )

    # Check if user exists
    response = user_table.get_item(Key={"username": username})
    if "Item" not in response:
        raise HTTPException(status_code=400, detail="User not found.")

    if new_tier == "free":
        # Update user's tier immediately
        user_table.update_item(
            Key={"username": username},
            UpdateExpression="SET tier = :new_tier",
            ExpressionAttributeValues={":new_tier": new_tier},
        )
        return {"free": True}

    # Generate a unique change ID
    change_id = str(uuid.uuid4())

    # Store pending tier change
    pending_tier_changes_table.put_item(
        Item={
            "change_id": change_id,
            "username": username,
            "new_tier": new_tier,
        }
    )

    # Create a new Stripe Checkout Session for the tier change
    try:
        # Create Checkout Session
        session = create_checkout_session(
            username, new_tier, change_id, is_change_tier=True, credits=credits_for_tier[new_tier]
        )
        return {"sessionId": session.id}
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        # Remove pending tier change if session creation fails
        pending_tier_changes_table.delete_item(Key={"change_id": change_id})
        raise HTTPException(
            status_code=500, detail="Failed to create checkout session."
        )


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        print("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"Checkout session completed: {session}")

        mode = session.get("mode")
        metadata = session.get("metadata", {})
        if mode == "subscription":
            if metadata.get("signup") == "true":
                # Retrieve the user ID
                user_id = session.get("client_reference_id")
                if not user_id:
                    print("No client_reference_id found.")
                    raise HTTPException(
                        status_code=400, detail="No client_reference_id found."
                    )

                # Retrieve user data from pending_users table
                response = pending_user_table.get_item(Key={"user_id": user_id})
                if "Item" not in response:
                    print("Pending user data not found.")
                    raise HTTPException(
                        status_code=400, detail="Pending user data not found."
                    )

                user_data = response["Item"]

                email = user_data["username"]
                tier = user_data["tier"]
                is_google_account = user_data.get("is_google_account", False)
                stripe_customer_id = session.get("customer")

                # Store user data in userbase table
                create_user(email, "", tier, stripe_customer_id, is_google_account)
                print(f"User {email} created in DynamoDB.")

                # Delete pending user data
                pending_user_table.delete_item(Key={"user_id": user_id})

            elif metadata.get("change_tier") == "true":
                # Handle tier change
                change_id = session.get("client_reference_id")
                credits = int(metadata.get("credits", 0))
                # Retrieve pending tier change data
                response = pending_tier_changes_table.get_item(
                    Key={"change_id": change_id}
                )
                if "Item" not in response:
                    print("Pending tier change data not found.")
                    raise HTTPException(
                        status_code=400, detail="Pending tier change data not found."
                    )
                change_data = response["Item"]
                username = change_data["username"]
                new_tier = change_data["new_tier"]
                # Update user's tier and credits in DynamoDB
                user_table.update_item(
                    Key={"username": username},
                    UpdateExpression="SET tier = :new_tier, exam_credits = exam_credits + :credits",
                    ExpressionAttributeValues={":new_tier": new_tier, ":credits": credits},
                )
                print(f"User {username} tier updated to {new_tier}.")

                # Delete pending tier change data
                pending_tier_changes_table.delete_item(Key={"change_id": change_id})
            else:
                print("Unknown subscription session.")
        elif mode == "payment":
            # Handle credits purchase
            metadata = session.get("metadata", {})
            username = metadata.get("username")
            credits = int(metadata.get("credits", 0))
            if not username or credits <= 0:
                print("Invalid metadata in payment session.")
                raise HTTPException(status_code=400, detail="Invalid payment metadata.")

            # Update user's credits in DynamoDB
            try:
                user_table.update_item(
                    Key={"username": username},
                    UpdateExpression="SET exam_credits = exam_credits + :credits",
                    ExpressionAttributeValues={":credits": credits},
                )
                print(f"Added {credits} credits to user {username}.")
            except Exception as e:
                print(f"Error updating user credits: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to update user credits."
                )
        else:
            print(f"Unhandled session mode: {mode}")

    # Return a 200 response to acknowledge receipt of the event
    return JSONResponse(status_code=200, content={"status": "success"})


@app.post("/grade_quiz")
async def grade_quiz(payload: dict):
    username = payload["username"]
    exam_id = payload["exam_id"]
    answers = payload["answers"]

    # Fetch user data
    response = user_table.get_item(Key={"username": username})
    item = response.get("Item")
    if item:
        exams = item.get("exams")
        exam = exams[exam_id]
        questions = exam["questions"]
        correct = 0
        total = len(questions)
        details = []
        user_tier = item.get("tier", "free")
        for i, question in enumerate(questions):
            answer = answers[str(i)]
            is_correct = False
            if question["type"] == "mc":
                is_correct = answer == question["correct_answer"]
            elif question["type"] == "oe":
                is_correct = isCorrectOpenEndedAnswer(
                    answer, question["correct_answer"], question["explanation"]
                )
            if is_correct:
                correct += 1
            # Prepare detail based on user's tier
            detail = {}
            if user_tier in ["gold", "diamond"]:
                detail["correct"] = is_correct
                detail["correct_answer"] = question["correct_answer"]
                if user_tier == "diamond":
                    detail["explanation"] = question["explanation"]
            details.append(detail)
        response = {"score": correct, "total": total}
        if user_tier in ["gold", "diamond"]:
            response["details"] = details
        return response
    else:
        return {"message": "User not found"}


# Wrap the FastAPI app with Mangum
# handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST"), port=int(os.getenv("PORT")))
