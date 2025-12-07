from openai import OpenAI


client = OpenAI(
    base_url="http://192.168.0.128:31100/v1",
    api_key="sk",
)

# completion = client.chat.completions.create(
#     model="myllm:latest",
#     messages=[
#         {"role": "developer", "content": "Talk like a pirate."},
#         {
#             "role": "user",
#             "content": "How do I check if a Python object is an instance of a class?",
#         },
#     ],
# )

# print(completion.choices[0].message.content)