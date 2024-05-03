from openai import OpenAI
import time
import requests
import json
import streamlit as st

news_api_key = "08456ce630c6420e863ab39a663c1ce6"

client = OpenAI()
model = "gpt-3.5-turbo"

def get_news(topic):
    url = (
        f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5"
    )

    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = json.dumps(response.json(), indent=4)
            news_json = json.loads(news)

            data = news_json

            # Access all the fields == loop through
            status = data["status"]
            totalResults = data["totalResults"]
            articles = data["articles"]
            final_news = []

            #loop
            for article in articles:
                source_name = article["source"]["name"]
                author = article["author"]
                title = article["title"]
                description = article["description"]
                url = article["url"]
                content = article["content"]
                title_descripton = f"""
                    Title: {title},
                    Author: {author},
                    Source: {source_name},
                    Description: {description},
                    Url: {url}
                """
                final_news.append(title_descripton)

            return final_news
        else:
            return []
        

    except requests.exceptions.RequestException as e:
        print("Error ocurred during API Request", e)

def get_reservas(matricula):
    url = f"https://apidream.azurewebsites.net/reserva/{matricula}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            reservas_json = response.json()

            final_reservas = []

            for reserva in reservas_json:
                id_reserva = reserva["id_reserva"]
                id_sala = reserva["id_sala"]
                id_proyecto = reserva["id_proyecto"]
                lider_reserva = reserva["lider_reserva"]
                fecha_generada = reserva["fecha_generada"]
                dia_reserva = reserva["dia_reserva"]
                hora_inicio = reserva["hora_inicio"]
                hora_final = reserva["hora_final"]
                nombre_proyecto = reserva["nombre_proyecto"]
                nombre_sala = reserva["nombre_sala"]

                reserva_info = f"""
                    ID Reserva: {id_reserva},
                    ID Sala: {id_sala},
                    ID Proyecto: {id_proyecto},
                    Líder de la Reserva: {lider_reserva},
                    Fecha Generada: {fecha_generada},
                    Día de la Reserva: {dia_reserva},
                    Hora de Inicio: {hora_inicio},
                    Hora Final: {hora_final},
                    Nombre del Proyecto: {nombre_proyecto},
                    Nombre de la Sala: {nombre_sala}
                """
                final_reservas.append(reserva_info)

            return final_reservas
        else:
            return []

    except requests.exceptions.RequestException as e:
        print("Error ocurred during API Request", e)

def crear_reserva(id_sala, id_proyecto, lider_reserva, dia_reserva, hora_inicio, hora_final, dispositivos):
    url = f"https://apidream.azurewebsites.net/reserva/creareserva"

    try:
        data = {
            "id_sala": id_sala,
            "id_proyecto": id_proyecto,
            "lider_reserva": lider_reserva,
            "dia_reserva": dia_reserva,
            "hora_inicio": hora_inicio,
            "hora_final": hora_final,
            "dispositivos": dispositivos
        }
        response = requests.post(url, json=data)  # Usamos json=data para enviar los datos como JSON
        if response.status_code == 200:
            print("Reserva creada con éxito.")
            return response.json()  # Devuelve la respuesta del servidor como JSON
        else:
            print("Error al crear la reserva.")
            return None

    except requests.exceptions.RequestException as e:
        print("Error ocurred during API Request", e)

class AssistantManager:
    thread_id = "thread_PJ674PKWPYEs9OK3sAV5u1bB"
    assistant_id = "asst_8868Xx2ENW0JGxsKtY3burgv"

    def __init__(self, model: str = model):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        #Rerieve existing assistant
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=self.model,
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"Assistant created with id: {self.assistant.id}")
    
    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"Thread created with id: {self.thread.id}")

    def start_run(self):
        if not self.run:
            run_obj = self.client.beta.threads.runs.create(
                thread_id=AssistantManager.thread_id
            )
            self.run = run_obj
            print(f"Run started with id: {self.run.id}")
        
    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
    
    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )
    
    def process_message(self):
        if self.run:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)
            
            self.summary = "\n".join(summary)
            print(f"Summary: {role.capitalize()}: ==> {response}")
    
    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "get_news":
                output = get_news(topic=arguments["topic"])
                print(f"STUFFF;;;;; {output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"],
                                     "output": final_str})
                
            elif func_name == "get_reservas":
                output = get_reservas(matricula=arguments["matricula"])
                print(f"STUFFF;;;;; {output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"],
                                     "output": final_str})
            
            elif func_name == "crear_reserva":
                output = crear_reserva(id_sala=arguments["id_sala"], id_proyecto=arguments["id_proyecto"], lider_reserva=arguments["lider_reserva"], dia_reserva=arguments["dia_reserva"], hora_inicio=arguments["hora_inicio"], hora_final=arguments["hora_final"], dispositivos=arguments["dispositivos"])
                print(f"STUFFF;;;;; {output}")
                final_str = "Reserva creada con éxito."

                tool_outputs.append({"tool_call_id": action["id"],
                                    "output": final_str})
                
            else:
                raise ValueError(f"Unknown function: {func_name}")
                
        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs
        )

    #for streamlit
    def get_summary(self):
        return self.summary

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id
                )
                print(f"RUN STATUS:: {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    print("FUNCTION CALLING NOW...")
                    self.call_required_functions(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )
    
    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id
        )
        print(f"Run steps: {run_steps}")

def main():
    manager = AssistantManager()

    # Streamlit interface
    st.title("Chatbot")

    with st.form(key="user_input_form"):
        instructions = st.text_input("Ingresa la matricula o los datos de la reserva:")
        submit_button = st.form_submit_button(label="Enviar")

        if submit_button:
            manager.create_assistant(
                name="News Summarizer",
                instructions="You are a personal article summarizer Assistant who knows how to take a list of articles and descriptions and then write a short summary of all the news articles, you also have the capability to take a matricula and retrieve the information of a reservation based on that or create a reservation. If the user asks for a reservation give them the following script: (Para reservar una sala, necesitarás proporcionar detalles específicos como la sala, id del proyecto ,matricula del lider del proyecto, el dia de la reserva, la hora de inicio y la hora de finalización.) ",
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_news",
                            "description": "Get the list of articles/news for the given topic",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "topic": {
                                        "type": "string",
                                        "description": "The topic for which you want to get the news"
                                    }
                                },
                                "required": ["topic"],
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_reservas",
                            "description": "Get the information of the reservation based on the matricula",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "matricula": {
                                        "type": "string",
                                        "description": "The matricula for which you want to get the reservation"
                                    }
                                },
                                "required": ["matricula"],
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "crear_reserva",
                            "description": "Posts a reservation with the id_sala, id_proyecto, lider_reserva, dia_reserva, hora_inicio, hora_final, dispositivos. If the user chooses Lego Room the id_sala is 1. If the user asks to create a reservation ask them for all of the parameters before posting anything.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "id_sala": {
                                        "type": "string",
                                        "description": "The id_sala for which you want to post the reservation, if they choose Lego Room change it to 1."
                                    },
                                    "id_proyecto": {
                                        "type": "string",
                                        "description": "The id_proyecto for which you want to post the reservation"
                                    },
                                    "lider_reserva": {
                                        "type": "string",
                                        "description": "The lider_reserva for which you want to post the reservation, the format must start with an A and is followed by 8 numbers, the format of the matricula is A00832807"
                                    },
                                    "dia_reserva": {
                                        "type": "string",
                                        "description": "The dia_reserva for which you want to post the reservation, it must take a year, month, day format like this, 2024-04-10"
                                    },
                                    "hora_inicio": {
                                        "type": "string",
                                        "description": "The hora_inicio for which you want to post the reservation. It must have this type of format 16:00:00.0000000, for example that is for 4pm"
                                    },
                                    "hora_final": {
                                        "type": "string",
                                        "description": "The hora_final for which you want to post the reservation. It must have this type of format 17:00:00.0000000, for example that is for 5pm"
                                    },
                                    "dispositivos": {
                                        "type": "string",
                                        "description": "The dispositivos for which you want to post the reservation, always put this one as null, with no information "
                                    }
                                },
                                "required": ["id_sala", "id_proyecto", "lider_reserva", "dia_reserva", "hora_inicio", "hora_final", "dispositivos"],
                            }
                        }
                    }
                ]
            )
            manager.create_thread()

            # Add the message and run the assistant
            manager.add_message_to_thread(
                role="user",
                content=f"summarize the news on this topic {instructions}"
            )
            manager.run_assistant(instructions="Summarize the news")

            # Wait for completions and process messages
            manager.wait_for_completion()

            summary = manager.get_summary()

            st.write(summary)
            
            st.text("Run steps:")
            st.code(manager.run_steps(), line_numbers=True)


if __name__ == "__main__":
    main()

