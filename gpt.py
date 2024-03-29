import requests
import transformers
from config import MAX_TOKENS, URL
import logging


prompts = {
    "математикалегкий": "Ты помощник для решения задач по математике. Объясняй простым языком. Пиши на русском",
    "математикапродвинутый": "Ты помощник для решения задач по математике. Объясняй продвинутым языком.Пиши на русском",
    "физикалегкий": "Ты помощник для решения задач по физике. Объясняй простым языком. Пиши на русском",
    "физикапродвинутый": "Ты помощник для решения задач по физике. Объясняй продвинутым языком. Пиши на русском",
}


def check_prompt_len(message):
    tokenizer = transformers.AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")
    return len(tokenizer.encode(message)) < MAX_TOKENS


def get_answer(subjectlevel, assistant_content="Решай задачу по шагам: ", request=""):
    response = requests.post(
        URL,
        headers={"Content-Type": "application/json"},
        json={
            "messages": [
                {"role": "user", "content": request},
                {"role": "system", "content": prompts.get(subjectlevel)},
                {"role": "assistant", "content": assistant_content},
            ],
            "temperature": 1.2,
            "max_tokens": MAX_TOKENS,
        }
    )
    resp = response.json()
    if response.status_code == 200 and "choices" in resp:
        return resp["choices"][0]["message"]["content"]
    else:
        logging.error(resp)
        return "Ошибка при генерации запроса"

