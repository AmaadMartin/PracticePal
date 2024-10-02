from exam_maker_agent import Agent

def main():
    agent = Agent()
    threadId = agent.create_conversation()
    agent.run_agent("Can you make a practice exam based on these class materials? Try to search as many files as possible for relevant information.", threadId)
    print(agent.data)

if __name__ == "__main__":
    main()