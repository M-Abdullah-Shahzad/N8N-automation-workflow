from dataclasses import dataclass
import time

@dataclass
class InputRow:
    full_name: str = ""
    email: str = ""
    password: str = ""
    phone: str = ""
    website: str = ""
    age: int | str = ""
    birthdate: str = ""
    appointment: str = ""
    alarm_time: str = ""
    color: str = ""
    satisfaction: str = ""
    volume: str = ""
    country: str = ""
    gender: str = ""
    education: str = ""
    hobbies: str = ""
    skills: str = ""
    terms: bool | str = False

    def __post_init__(self):
        self.full_name = str(self.full_name).strip().title()
        self.email = str(self.email).strip().lower()
        self.password = str(self.password).strip()
        self.phone = str(self.phone).strip()
        self.website = str(self.website).strip()
        self.birthdate = str(self.birthdate).strip()
        self.appointment = str(self.appointment).strip()
        self.alarm_time = str(self.alarm_time).strip()
        self.color = str(self.color).strip()
        self.satisfaction = float(str(self.satisfaction).strip())
        self.volume = float(str(self.volume).strip())
        self.country = str(self.country).strip().title()
        self.gender = str(self.gender).strip().title()
        self.education = str(self.education).strip()
        self.hobbies = str(self.hobbies).strip()
        self.skills = str(self.skills).strip()

        if self.age != "":
            self.age = int(self.age)

        if isinstance(self.terms, str):
            self.terms = self.terms.strip().lower() in {"true", "1", "yes", "on", "checked"}