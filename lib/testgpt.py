import json
from pathlib import Path

import openai
from openai import RateLimitError


class TestGPT:
    def __init__(self, config_file="testgpt_prompting.json"):
        self.api_key = ""  # <------------ VOEG HIER JE API-KEY IN <-----------

        self.config_file = config_file
        if not hasattr(openai, "chat"):
            raise Exception(
                "Old version of the openai library, please upgrade to the latest version using the 'pip install openai --upgrade' command"
            )

        self.initial_parameters = self.get_initial_parameters()
        self.init_openai()

    def init_openai(self):
        openai.api_key = self.api_key
        # Dit zou een goede plek zijn om meer openai parameters te zetten

    def get_initial_parameters(self):
        self_path = Path(globals().get("__file__", "./_")).absolute().parent
        config_file = self_path / self.config_file
        with open(config_file) as f:
            return json.load(f)

    def _generate_question(self, prompt, question_type):
        if question_type not in self.initial_parameters["prompts"]:
            raise ValueError(
                f"Question type {question_type} not found in config file {self.config_file}"
            )
        if not prompt:
            raise ValueError("The given note was empty, we can't ask empty questions")
        parameters = {
            "model": self.initial_parameters["model"],
            "messages": self.initial_parameters["prompts"][question_type]["messages"],
        }
        parameters["messages"].append({"role": "user", "content": prompt})
        result = None
        try:
            response = openai.chat.completions.create(**parameters)
            result = response.choices[0].message.content
        except RateLimitError as e:
            if e.code == "insufficient_quota":
                raise Exception(
                    "You have reached the rate limit, or your account is out of credits."
                    " Consider using the 'FakeTestGPT' class."
                )
        return result

    def generate_open_question(self, prompt):
        return self._generate_question(prompt, "open_question")

    def generate_multiple_choice_question(self, prompt):
        return self._generate_question(prompt, "multiple_choice_question")

    def generate_open_answer(self, prompt):
        return self._generate_question(prompt, "open_answer")

    def generate_multiple_answer(self, prompt):
        return self._generate_question(prompt, "multiple_answer")


class FakeTestGPT(TestGPT):
    def generate_open_question(self, prompt):
        return "Wat is de hoofdstad van Nederland?"

    def generate_multiple_choice_question(self, promt):
        return "Wat is de hoofdstad van Nederland?"

    def generate_open_answer(self, prompt):
        return "De hoofdstad van nederland is Amsterdam"

    def generate_multiple_answer(self, prompt):
        return "\n A) Amsterdam\n B) Den Haag\n C) Rotterdam\n D) Utrecht"


if __name__ == "__main__":
    api_key = "hatsieflatsiekidee"
    test_gpt = TestGPT(api_key)
    test_text = """
De grutto is een oer-Hollandse weidevogel. Je vindt deze grote, slanke steltloper op erven en graslanden van
 boerenbedrijven waar voldoende ruimte is voor natuur. Het meest ideaal zijn vochtige, kruidenrijke graslanden met een
  goed bodemleven en volop insecten aan de oppervlakte.
"""
    try:
        test_result = test_gpt.generate_open_question(test_text)
        print(test_result)
        test_result = test_gpt.generate_multiple_choice_question(test_text)
        print(test_result)
    except Exception as e:
        print(e)

    # Hier testen we nog een keer, maar met de "FakeTestGPT" class, die geen echte openai calls doet
    try:
        test_gpt = FakeTestGPT(api_key)
        test_result = test_gpt.generate_open_question(test_text)
        print(test_result)
        test_result = test_gpt.generate_multiple_choice_question(test_text)
        print(test_result)
    except Exception as e:
        print(e)