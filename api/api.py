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


def create_user(email, password, tier, stripe_customer_id=None):
    match tier:
        case "free":
            exam_credits = 6
        case "gold":
            exam_credits = 15
        case "diamond":
            exam_credits = 50
    user_table.put_item(
        Item={
            "username": email,
            "password": password,
            "stripe_customer_id": "",
            "tier": tier,
            "exams": [],
            "exam_credits": exam_credits,
        }
    )


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


def create_checkout_session(email, tier, user_id):
    # Map subscription tiers to Stripe Price IDs
    price_ids = {
        "free": os.getenv("STRIPE_FREE_PRICE"),  # Replace with your actual Price IDs
        "gold": os.getenv("STRIPE_GOLD_PRICE"),
        "diamond": os.getenv("STRIPE_DIAMOND_PRICE"),
    }
    if tier not in price_ids:
        raise ValueError("Invalid subscription tier: " + tier)

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
        client_reference_id=user_id,  # Pass the unique user ID
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
        raise HTTPException(status_code=500, detail="Failed to create checkout session.")


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
        if mode == "subscription":
            # Handle subscription sign up
            # Existing code
            # Retrieve the user ID
            user_id = session.get("client_reference_id")
            if not user_id:
                print("No client_reference_id found.")
                raise HTTPException(status_code=400, detail="No client_reference_id found.")

            # Retrieve user data from pending_users table
            response = pending_user_table.get_item(Key={"user_id": user_id})
            if "Item" not in response:
                print("Pending user data not found.")
                raise HTTPException(status_code=400, detail="Pending user data not found.")

            user_data = response["Item"]

            email = user_data["username"]
            password_hash = user_data["password"]
            tier = user_data["tier"]
            stripe_customer_id = session.get("customer")

            # Store user data in userbase table
            create_user(email, password_hash, tier, stripe_customer_id)
            print(f"User {email} created in DynamoDB.")

            # Delete pending user data
            pending_user_table.delete_item(Key={"user_id": user_id})

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
                raise HTTPException(status_code=500, detail="Failed to update user credits.")
        else:
            print(f"Unhandled session mode: {mode}")

    # Return a 200 response to acknowledge receipt of the event
    return JSONResponse(status_code=200, content={"status": "success"})

@app.post("/grade_quiz")
async def grade_quiz(payload: dict):
    print(payload["username"])
    print(payload["exam_id"])
    print(payload["answers"])
    print(payload)

    # test_response = {
    #     "score": 3,
    #     "total": 4,
    #     "details": [
    #         {
    #             "correct_answer": "Paris",
    #             "explanation": "Paris is the capital of France.",
    #             "correct": True
    #         },
    #                     {
    #             "correct_answer": "Paris",
    #             "explanation": "Paris is the capital of France.",
    #             "correct": False
    #         }
    #     ]
    # }
    # return test_response

    response = user_table.get_item(Key={"username": payload["username"]})
    item = response.get("Item")
    if item:
        exams = item.get("exams")
        exam = exams[payload["exam_id"]]
        questions = exam["questions"]
        correct = 0
        total = len(questions)
        details = []
        for i, question in enumerate(questions):
            answer = payload["answers"][str(i)]
            if question["type"] == "mc":
                correct += 1 if answer == question["correct_answer"] else 0
                details.append(
                    {
                        "correct_answer": question["correct_answer"],
                        "explanation": question["explanation"],
                        "correct": answer == question["correct_answer"],
                    }
                )
            elif question["type"] == "oe":
                isCorrect = isCorrectOpenEndedAnswer(
                    answer, question["correct_answer"], question["explanation"]
                )
                correct += 1 if isCorrect else 0
                details.append(
                    {
                        "correct_answer": question["correct_answer"],
                        "explanation": question["explanation"],
                        "correct": isCorrect,
                    }
                )
        response = {"score": correct, "total": total, "details": details}
        return response
    else:
        return {"message": "User not found"}


# Wrap the FastAPI app with Mangum
# handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST"), port=int(os.getenv("PORT")))
