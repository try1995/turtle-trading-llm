from llm import client

sys_prompt = """You are an planner agent.
    Your job is to decide which agents to run based on the user's request.
                      Provide your response in JSON format with the following structure:
{'main_task': 'Plan a family trip from Singapore to Melbourne.',
 'subtasks': [{'assigned_agent': 'flight_booking',
               'task_details': 'Book round-trip flights from Singapore to '
                               'Melbourne.'}
    Below are the available agents specialised in different tasks:
    - FlightBooking: For booking flights and providing flight information
    - HotelBooking: For booking hotels and providing hotel information
    - CarRental: For booking cars and providing car rental information
    - ActivitiesBooking: For booking activities and providing activity information
    - DestinationInfo: For providing information about destinations
    - DefaultAgent: For handling general requests"""


class PlanAgent:
    def invork(self, message):
        stream = client.chat.completions.create(
            model="myllm:latest",
            messages=[
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": message
                },
            ],
            stream=True,
        )
        for event in stream:
            print(event.choices[0].delta.content, end="")

