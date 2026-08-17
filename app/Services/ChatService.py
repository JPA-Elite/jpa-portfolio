import os
import re
import time
from datetime import datetime

from flask_babel import gettext, get_locale

from app.Services.KnowledgeBaseService import KnowledgeBaseService
from app.configurations import SortOrder

CHAT_MATCH_THRESHOLD = 0.36
CHAT_SUGGEST_THRESHOLD = 0.28

CHAT_SESSION_TTL_SECONDS = 3600
CHAT_SESSION_MAX_COUNT = 300
CHAT_SESSION_MAX_TURNS = 24

CHAT_COVERAGE_THRESHOLD = 0.5
CHAT_FUZZY_WORD_RATIO = 0.8
CHAT_KB_GUARD_THRESHOLD = 0.62

DYNAMIC_KB_QUESTIONS = {"What is your job?"}

CHAT_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
    "do", "does", "did", "doing", "what", "whats", "which", "when", "where",
    "who", "whom", "whose", "why", "how", "your", "yours", "you", "yourself",
    "i", "me", "my", "mine", "myself", "we", "us", "our", "ours",
    "he", "she", "him", "her", "his", "hers", "it", "its", "they", "them", "their", "theirs",
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "up", "down", "out", "off", "over", "under",
    "and", "or", "but", "not", "no", "nor", "so", "than", "too", "very", "just",
    "can", "could", "would", "should", "shall", "will", "please", "tell", "about",
    "that", "this", "these", "those", "there", "here", "want", "know", "need",
    "ang", "mga", "nga", "ug", "sa", "kay", "na", "pa", "ba", "ng", "ay",
    "ako", "ko", "ka", "ikaw", "akong", "imong", "iyang", "mo",
    "kini", "kana", "kanang", "didto", "diri", "namo", "nila", "sila",
    "ito", "iyan", "iyon", "doon", "dito", "si", "sina", "para", "may",
    "pero", "kung", "kapag", "niya", "kanila",
}

CHAT_ALIASES = {
    "What is your name?": [
        "who are you", "introduce yourself", "your name", "name", "what is your full name",
        "full name", "tell me your name", "what's your name",
    ],
    "What is your age?": [
        "how old", "years old", "age", "born", "birthday", "birthdate", "year born",
        "how old are you",
    ],
    "What do you call yourself?": [
        "nickname", "call you", "nicknames", "what should i call you", "your nickname",
    ],
    "What is your job?": [
        "what do you do", "occupation", "profession", "work", "job", "job title",
        "what do you do for a living", "your job", "what is your work",
    ],
    "What is your favorite sport?": [
        "favorite sport", "sport", "basketball", "hobby", "games", "play", "what sport",
        "favorite hobby", "what do you play",
    ],
    "What is your favorite subject?": [
        "favorite subject", "subject", "math", "school subject", "favorite class",
        "what subject",
    ],
    "Where do you live?": [
        "where do you live", "where are you from", "location", "address", "hometown",
        "home", "where you live", "your hometown", "from where", "where do you stay",
    ],
    "What is your dream job?": [
        "dream job", "dream", "aspiration", "future job", "become", "what do you want to be",
        "dream career",
    ],
    "What type of person are you?": [
        "type of person", "personality", "describe yourself", "introvert", "behavior",
        "character", "what kind of person",
    ],
    "What is your favorite programming language?": [
        "programming language", "programming", "coding", "code", "python", "language",
        "favorite language", "what language", "what programming language",
    ],
}

CHAT_ALIASES_LOCALIZED = {
    "ceb": {
        "What is your name?": ["kinsa ka", "unsa imong pangalan", "pangalan"],
        "What is your age?": ["pila imong edad", "edad", "panuigon"],
        "What is your job?": ["unsa imong trabaho", "trabaho"],
        "What is your favorite sport?": ["paborito nga dula", "paborito nga sports"],
        "Where do you live?": ["asa ka nagpuyo", "asa ka taga", "puy-anan", "tagadiha"],
        "What is your dream job?": ["pangandoy nga trabaho", "pangandoy"],
        "What type of person are you?": ["unsa nga klase sa tao", "klase sa tao"],
        "What is your favorite programming language?": ["paborito nga programming language", "paborito nga language"],
    },
    "fil_PH": {
        "What is your name?": ["sino ka", "ano pangalan mo", "pangalan"],
        "What is your age?": ["ilang taon mo", "edad"],
        "What is your job?": ["ano trabaho mo", "trabaho"],
        "What is your favorite sport?": ["paborito mong laro", "laro"],
        "Where do you live?": ["saan ka nakatira", "taga saan"],
        "What is your dream job?": ["pangarap na trabaho", "pangarap"],
        "What type of person are you?": ["anong klaseng tao", "klase ng tao"],
        "What is your favorite programming language?": ["paborito mong programming language", "paboritong language"],
    },
    "fr": {
        "What is your name?": ["comment tu t'appelles", "ton nom", "quel est ton nom"],
        "What is your age?": ["quel age as tu", "ton age"],
        "What is your job?": ["quel est ton travail", "ton metier", "c'est quoi ton travail"],
        "What is your favorite sport?": ["ton sport prefere", "sport prefere"],
        "Where do you live?": ["ou habites tu", "tu habites ou", "d'ou viens tu"],
        "What is your dream job?": ["ton reve", "metier de reve"],
        "What type of person are you?": ["quel genre de personne"],
        "What is your favorite programming language?": ["ton langage de programmation prefere", "langage prefere"],
    },
}

FOLLOW_UP_MORE_PATTERNS = [
    "tell me more", "more details", "more info", "more information", "details",
    "elaborate", "elaborate more", "explain more", "expand", "go on", "continue",
    "and then", "more about", "what else", "anything else", "tell me about it",
    "talk more", "keep going", "give me more", "more",
]

FOLLOW_UP_WHICH_PATTERNS = [
    "which one", "which of them", "which of these", "which one is",
    "how about", "what about", "pick one", "choose one",
]

ORDINAL_WORDS = {
    "first": 0, "1st": 0,
    "second": 1, "2nd": 1,
    "third": 2, "3rd": 2,
    "fourth": 3, "4th": 3,
    "fifth": 4, "5th": 4,
    "sixth": 5, "6th": 5,
}

SENSITIVE_WORDS = {
    "password", "passcode", "secret", "secret key", "api key", "apikey",
    "access token", "token", "oauth", "credential", "credentials", "private key",
    "ssh", "login", "auth", "session id", "cookie", "credit card", "debit card",
    "card number", "cvv", "cvc", "bank account", "banking", "ssn", "social security",
    "national id", "passport",
}

EMOJI_ONLY_PATTERN = re.compile(
    r"[\U0001F000-\U0001FAFF\U0001F900-\U0001F9FF\u2600-\u27BF\u2B50\u2764\uFE0F\u2728]"
)

GREETING_PATTERNS = [
    "hi", "hello", "hey", "hola", "kumusta",
    "good morning", "good afternoon", "good evening", "good day",
]

QUICK_QUESTIONS_PATTERNS = [
    "suggested questions",
    "quick questions",
    "what can you answer",
    "what can i ask",
    "what can you do",
    "show the questions",
    "list the questions",
    "what are the options",
    "help",
]

FAREWELL_PHRASES = [
    "bye", "goodbye", "see you", "see ya", "farewell", "good night", "talk to you later",
]

APPRECIATION_PHRASES = [
    "thanks", "thank you", "thank", "awesome", "amazing", "excellent", "wow", "cool",
    "great", "nice", "nice one", "love it", "loved it", "liked it", "appreciate it",
    "brilliant", "perfect", "helpful", "well done", "good job", "good answer",
    "that's good", "thats good", "very good", "so good",
]

HOW_ARE_YOU_PATTERNS = [
    "how are you", "how's it going", "hows it going", "how are you doing",
    "you good", "how have you been", "how is it going", "how are u",
]

GIRLFRIEND_PATTERNS = [
    "girlfriend", "girl friend", "gf", "fiona", "samantha", "escarro",
]

GIRLFRIEND_PRIVATE_PATTERNS = [
    "contact", "contacts", "contact number", "number", "phone", "cellphone",
    "cell phone", "mobile", "email", "address", "facebook", "instagram",
    "messenger", "whatsapp", "tiktok", "social media", "socials", "reach",
]

GIRLFRIEND_COMPANY_WORDS = [
    "company", "which company", "what company", "her company",
    "employer", "where does she work", "where do she work", "where she works",
]

GIRLFRIEND_AGE_WORDS = [
    "age", "how old", "years old", "year old", "old", "birthday", "birthdate",
    "born", "edad", "panuigon", "taon", "anyos",
]

GIRLFRIEND_BIRTHDAY = datetime(2005, 4, 11)

UNRELATED_PATTERNS = [
    "1 + 1", "1+1", "2 + 2", "2+2", "3 + 3", "4 + 4", "5 + 5", "10 + 10",
    "plus", "minus", "multiply", "multiplied", "divided by", "divide", "division",
    "equation", "calculate", "calculator", "solve", "math problem", "math question",
    "weather", "temperature", "forecast", "is it raining", "is it sunny",
    "recipe", "cooking", "bake", "baking", "ingredients",
    "translate", "translation",
    "capital of", "population of", "currency of",
]

PROJECTS_PATTERNS = [
    "projects", "project", "what have you built", "what did you build", "your works",
    "portfolio projects", "key projects", "what do you build",
]

EXPERIENCE_PATTERNS = [
    "your experience", "work history", "where did you work", "where have you worked",
    "companies you worked", "your job history", "career journey", "company roadmap",
    "roadmap", "internship", "intern",
]

SUMMARY_PATTERNS = [
    "years of experience", "years of coding", "how many projects", "how experienced",
    "experience level", "your stats", "projects shipped",
]

ABOUT_PATTERNS = [
    "tell me about yourself", "about you", "about yourself", "tell me about you",
]

CERTIFICATIONS_PATTERNS = [
    "certifications", "certification", "certificates", "certs", "certified",
]

EDUCATION_PATTERNS = [
    "education", "school", "resume", "degree", "where did you study", "college",
    "academic", "university", "studied",
]

GALLERY_PATTERNS = [
    "gallery", "photos", "pictures", "your photos", "photographs", "images",
]

VLOG_PATTERNS = [
    "vlog", "vlogs", "videos", "your vlog", "video", "watch",
]

MUSIC_PATTERNS = [
    "music", "songs", "playlist", "favorite music", "song", "your music",
    "artist", "artists", "who sings", "who composed", "who wrote the song",
]

DONATION_PATTERNS = [
    "donate", "donation", "support you", "send a gift", "contribution", "donate money",
    "gift",
]

BOOKING_PATTERNS = [
    "book", "booking", "book you", "appointment", "hire", "services", "rates",
    "consultation", "session", "schedule", "employ",
]

CONCERN_PATTERNS = [
    "concern", "feedback", "complaint", "share your thoughts", "give feedback",
    "report", "suggestion",
]

QR_CODE_PATTERNS = [
    "qr", "qr code", "qrcode",
]

SURVEY_LINK_PATTERNS = [
    "survey link", "survey url", "survey button", "take the survey",
    "google form", "google forms", "forms.gle", "the survey",
]

SURVEY_URL_DEFAULT = "https://forms.gle/QV5kHc3STEFDFUYf9"
SURVEY_URL_PROFESSIONAL = "https://forms.gle/5UqVgzzxgkJS11Qj9"

URL_QUESTION_PATTERNS = [
    "what is the url", "whats the url", "what is url", "whats url", "whats your url",
    "what is your url", "what is the link", "whats the link", "what is link",
    "what is your website", "whats your website",
    "the url for", "the url of", "url for", "url of",
    "the link for", "the link of", "link for", "link of",
    "give me the url", "give me the link", "send me the url", "send me the link",
    "send the url", "send the link",
    "where can i find", "where do i find",
    "take me to", "how do i go to", "how to go to",
    "link to the", "url to the",
]

SOCIAL_LINK_WORDS = [
    "facebook", "instagram", "linkedin", "github", "twitter", "social", "email",
]

PAGE_TOPIC_KEYWORDS = [
    ("donation", ["donation", "donate", "qr"]),
    ("gallery", ["gallery", "photos", "pictures"]),
    ("vlog", ["vlog", "video"]),
    ("music", ["music", "song"]),
    ("build", ["booking", "book", "build", "hire", "appointment", "schedule", "consultation"]),
    ("concern", ["concern", "feedback", "complaint"]),
    ("portfolio", ["portfolio", "project", "projects", "resume"]),
    ("home", ["home", "website", "site"]),
]

PAGE_PATHS = {
    "home": "/",
    "portfolio": "/portfolio",
    "gallery": "/gallery",
    "vlog": "/vlog",
    "music": "/music",
    "donation": "/donation",
    "build": "/build",
    "concern": "/concern",
}

TOPIC_HANDLERS = [
    ("summary", SUMMARY_PATTERNS, "_topic_summary"),
    ("about", ABOUT_PATTERNS, "_topic_about"),
    ("projects", PROJECTS_PATTERNS, "_topic_projects"),
    ("experience", EXPERIENCE_PATTERNS, "_topic_experience"),
    ("certifications", CERTIFICATIONS_PATTERNS, "_topic_certifications"),
    ("education", EDUCATION_PATTERNS, "_topic_education"),
    ("gallery", GALLERY_PATTERNS, "_topic_gallery"),
    ("vlog", VLOG_PATTERNS, "_topic_vlog"),
    ("music", MUSIC_PATTERNS, "_topic_music"),
    ("donation", DONATION_PATTERNS, "_topic_donation"),
    ("booking", BOOKING_PATTERNS, "_topic_booking"),
    ("concern", CONCERN_PATTERNS, "_topic_concern"),
]

TOPIC_METHODS = {name: method for name, _, method in TOPIC_HANDLERS}

DEVELOPERS_PATTERNS = [
    "who made this", "who built this", "who developed this", "who created this",
    "who designed", "credits", "who made the site",
    "who made this website", "who built the website",
]

IDENTITY_PATTERNS = [
    "who made you", "who created you", "who built you", "are you a robot",
    "are you real", "are you ai", "are you an ai", "are you human", "are you a bot",
]

NEGATIVE_PHRASES = [
    "that's wrong", "thats wrong", "not helpful", "bad answer", "you're wrong",
    "youre wrong", "incorrect", "useless", "wrong answer", "doesn't work",
]

JOKE_PATTERNS = [
    "tell me a joke", "make me laugh", "say something funny", "a joke", "joke", "funny",
]

REDIRECT_PHRASES = [
    "i don't understand", "i dont understand", "what do you mean", "i don't get it",
    "i dont get it", "confused", "im lost", "im confused", "i'm confused",
]

NOISE_PREFIXES = [
    "please tell me", "can you tell me", "could you tell me", "do you know",
    "i want to know", "i would like to know", "can i know", "hey", "hello", "hi",
    "well", "so",
]

CONTRACTIONS = {
    "wats": "what is", "whats": "what is", "wat": "what", "wut": "what",
    "wheres": "where is", "whre": "where", "where'd": "where did",
    "ur": "your", "u": "you", "im": "i am", "dont": "do not",
    "doesnt": "does not", "didnt": "did not", "cant": "can not",
    "thats": "that is", "wouldnt": "would not", "wanna": "want to",
    "gonna": "going to", "pls": "please", "plz": "please", "hows": "how is",
}


class ChatService:
    def __init__(
        self,
        key_project_service=None,
        company_roadmap_service=None,
        gallery_service=None,
        video_service=None,
        music_service=None,
        knowledge_base_service=None,
        gemini_service=None,
    ):
        self.key_project_service = key_project_service
        self.company_roadmap_service = company_roadmap_service
        self.gallery_service = gallery_service
        self.video_service = video_service
        self.music_service = music_service
        self.knowledge_base_service = knowledge_base_service
        self.gemini_service = gemini_service
        self._kb_cache = None
        self._locale = "en"
        self._session_id = None
        self._last_topic = None
        self._last_item = None
        self._last_reply_items = None
        self._sessions = {}

    def _knowledge_base(self):
        if self._kb_cache is None:
            self._kb_cache = self.knowledge_base_service or KnowledgeBaseService()
        return self._kb_cache

    def _kb_section_by_key(self, key):
        for section in self._knowledge_base().sections():
            if section.get("key") == key:
                return section
        return None

    def _kb_section_reply(self, key, fallback_key):
        locale = self._locale
        try:
            locale = get_locale() or locale
        except Exception:
            pass
        section = self._kb_section_by_key(key)
        if section:
            localized = section.get("localized") or {}
            loc = localized.get(locale) or {}
            body = loc.get("body") or section.get("body")
            if body:
                return body
        return gettext(fallback_key)

    def get_qa_data(self):
        try:
            locale = get_locale() or "en"
        except Exception:
            locale = self._locale or "en"
        return [
            self._qa_item(section, locale)
            for section in self._knowledge_base().sections()
        ]

    def _qa_item(self, section, locale):
        localized = section.get("localized") or {}
        loc = localized.get(locale) or {}
        question = loc.get("heading") or section["heading"]
        answer = loc.get("body") or section["body"]
        if question in DYNAMIC_KB_QUESTIONS:
            dynamic = self._current_company_reply()
            if dynamic:
                answer = dynamic
        aliases = list(section["aliases"])
        for alias in loc.get("aliases") or []:
            if alias not in aliases:
                aliases.append(alias)
        return {
            "question": question,
            "answer": answer,
            "aliases": aliases,
            "source_heading": section["heading"],
        }

    def _collect_aliases(self, item):
        q_text = item.get("question") or ""
        aliases = list(CHAT_ALIASES.get(q_text, []))
        aliases.extend(item.get("aliases") or [])
        langs = [self._locale]
        if self._locale in ("ceb", "fil_PH"):
            langs.append("fil_PH" if self._locale == "ceb" else "ceb")
        for lang in langs:
            aliases.extend(CHAT_ALIASES_LOCALIZED.get(lang, {}).get(q_text, []))
        return aliases

    def _kb_answer_for(self, item):
        if item.get("source_heading") in DYNAMIC_KB_QUESTIONS:
            dynamic = self._current_company_reply()
            if dynamic is not None:
                return dynamic
        return item.get("answer")

    def _current_roadmap_entry(self, entries):
        if not entries:
            return None
        present = [
            entry for entry in entries
            if "present" in str(entry.get("period") or "").lower()
        ]
        pool = present or entries
        return max(pool, key=lambda entry: entry.get("sort_order") or 0)

    def _current_company_reply(self):
        if self.company_roadmap_service is None:
            return None
        try:
            items = self.company_roadmap_service.get_active_company_roadmaps()
        except Exception:
            return None
        entries = [self._as_dict(item) for item in (items or [])]
        current = self._current_roadmap_entry(entries)
        if not current:
            return None
        role = self._localize_roadmap_role(current)
        company = str(current.get("company_name") or "").strip()
        if not role or not company:
            return None
        return gettext("chat_current_role_reply").format(role=role, company=company)

    def _kb_match(self, expanded):
        qa = self.get_qa_data()
        best = self._find_best_qa(expanded, qa)
        if best and best["score"] >= CHAT_KB_GUARD_THRESHOLD:
            return self._reply(
                self._apply_age(self._kb_answer_for(best["qa"])),
                matched_question=best["qa"]["question"],
            )
        return None

    def _is_count_question(self, expanded):
        if any(word in expanded for word in ["how many", "count", "number of", "total"]):
            return True
        if self._locale == "ceb" and any(word in expanded for word in ["pila", "tagpila", "pila ka"]):
            return True
        if self._locale == "fil_PH" and any(word in expanded for word in ["ilan", "ilan ba", "gaano karami"]):
            return True
        return False

    def resolve(self, message, qa_data=None, session_id=None):
        message = (message or "").strip()
        self._session_id = session_id or None
        self._last_topic = None
        self._last_item = None
        self._last_reply_items = None
        if not message:
            return self._reply(gettext("chat_unknown_fallback"))

        try:
            self._locale = get_locale() or "en"
        except Exception:
            self._locale = "en"

        normalized = message.lower()
        expanded = self._normalize_spacing(self._expand_message(normalized))
        self._prune_sessions()
        self._remember_user(message)

        if self._is_sensitive(normalized):
            return self._reply(gettext("chat_sensitive_refusal"), action="expand_options")

        if self._is_emoji_only(normalized):
            return self._reply(gettext("chat_emoji_only_reply"))

        if self._is_quick_questions(normalized):
            questions = " • ".join(item["question"] for item in (qa_data or self.get_qa_data())[:10])
            return self._reply(
                f"{gettext('chat_quick_questions_intro')} {questions}",
                action="expand_options",
            )

        if self._is_greeting(normalized):
            return self._reply(gettext("chat_greeting_fallback"))

        if self._is_farewell(normalized):
            return self._reply(gettext("chat_farewell_reply"))

        if self._is_appreciation(normalized):
            return self._reply(gettext("chat_appreciation_reply"))

        if self._is_how_are_you(expanded):
            return self._reply(gettext("chat_how_are_you_reply"))

        if self._is_qr_question(normalized):
            return self._reply(gettext("chat_qr_reply").format(url=self._site_url(PAGE_PATHS["donation"])))

        survey_reply = self._resolve_survey_question(normalized)
        if survey_reply:
            return self._reply(survey_reply)

        url_reply = self._resolve_url_question(normalized)
        if url_reply:
            return self._reply(url_reply)

        girlfriend_contact = self._resolve_girlfriend_contact(normalized)
        if girlfriend_contact:
            return self._reply(girlfriend_contact)

        girlfriend_followup_contact = self._resolve_girlfriend_followup_contact(normalized)
        if girlfriend_followup_contact:
            return self._reply(girlfriend_followup_contact)

        girlfriend_company = self._resolve_girlfriend_company(normalized)
        if girlfriend_company:
            return self._reply(girlfriend_company)

        girlfriend_followup_company = self._resolve_girlfriend_followup_company(normalized)
        if girlfriend_followup_company:
            return self._reply(girlfriend_followup_company)

        girlfriend_age = self._resolve_girlfriend_age(normalized)
        if girlfriend_age:
            return self._reply(girlfriend_age)

        girlfriend_followup_age = self._resolve_girlfriend_followup_age(normalized)
        if girlfriend_followup_age:
            return self._reply(girlfriend_followup_age)

        if self._is_girlfriend_question(normalized):
            self._last_topic = "girlfriend"

        if self._is_unrelated(normalized, expanded):
            return self._reply(gettext("chat_unrelated_reply"))

        ai_answer = self._ai_chat_answer(message)
        if ai_answer:
            return self._reply(ai_answer)

        girlfriend_reply = self._resolve_girlfriend(normalized)
        if girlfriend_reply:
            return self._reply(girlfriend_reply)

        girlfriend_followup = self._resolve_girlfriend_followup(normalized)
        if girlfriend_followup:
            return self._reply(girlfriend_followup)

        content = self._resolve_content(normalized, expanded)
        if content:
            return content

        if self._is_developers(normalized):
            return self._reply(gettext("chat_developers_reply"))

        contact = self._is_contact(expanded)
        if contact:
            return self._reply(contact)

        skills = self._is_skills(expanded)
        if skills:
            return self._reply(skills)

        if self._is_identity(normalized):
            return self._reply(gettext("chat_identity_reply"))

        if self._is_negative(normalized):
            return self._reply(gettext("chat_negative_reply"))

        if self._is_joke(normalized):
            return self._reply(gettext("chat_joke_reply"))

        if self._is_redirect(normalized):
            return self._reply(gettext("chat_redirect_reply"), action="expand_options")

        followup = self._resolve_follow_up(normalized, expanded)
        if followup:
            return followup

        topic = self._search_topics_content(expanded)
        if topic:
            return getattr(self, TOPIC_METHODS[topic])(normalized, expanded)

        fuzzy = self._fuzzy_topic_match(normalized)
        if fuzzy:
            return getattr(self, fuzzy[2])(normalized, expanded)

        qa = qa_data if qa_data is not None else self.get_qa_data()

        exact = self._get_exact_answer(message, qa)
        if exact:
            return self._reply(exact, matched_question=message)

        best = self._find_best_qa(expanded, qa)
        if best and best["score"] >= CHAT_MATCH_THRESHOLD:
            return self._reply(
                self._apply_age(self._kb_answer_for(best["qa"])),
                matched_question=best["qa"]["question"],
            )

        if best and best["score"] >= CHAT_SUGGEST_THRESHOLD:
            suggestions = self._suggest_questions(expanded, qa)
            return self._reply(
                f"{gettext('chat_did_you_mean')} {' • '.join(suggestions)}",
                action="expand_options",
            )

        suggested = self._suggest_follow_ups(qa)
        if suggested:
            return self._reply(suggested, action="expand_options")

        return self._reply(
            f"{gettext('chat_unknown_fallback_intro')} {gettext('chat_unknown_fallback')}"
        )

    def _reply(self, answer, action=None, matched_question=None):
        result = {"answer": answer, "action": action, "matched_question": matched_question}
        self._remember_turn(result)
        return result

    # ------------------------------ intents ------------------------------

    def _is_sensitive(self, normalized):
        return any(self._contains_word(normalized, word) for word in SENSITIVE_WORDS)

    def _is_quick_questions(self, normalized):
        return any(pattern in normalized for pattern in QUICK_QUESTIONS_PATTERNS)

    def _is_emoji_only(self, normalized):
        if not normalized:
            return False
        if re.search(r"[a-z0-9]", normalized):
            return False
        return EMOJI_ONLY_PATTERN.search(normalized) is not None

    def _is_greeting(self, normalized):
        return any(self._contains_word(normalized, word) for word in GREETING_PATTERNS)

    def _is_farewell(self, normalized):
        return any(self._contains_word(normalized, word) for word in FAREWELL_PHRASES)

    def _is_appreciation(self, normalized):
        return any(self._contains_word(normalized, word) for word in APPRECIATION_PHRASES)

    def _is_how_are_you(self, normalized):
        return any(self._contains_word(normalized, word) for word in HOW_ARE_YOU_PATTERNS)

    def _is_developers(self, normalized):
        return any(self._contains_word(normalized, word) for word in DEVELOPERS_PATTERNS)

    def _is_contact(self, normalized):
        if any(self._contains_word(normalized, word) for word in BOOKING_PATTERNS + ["contact", "email", "social media", "facebook", "instagram", "linkedin", "github", "reach you", "phone number", "get in touch"]):
            self._last_topic = "contact"
            return self._kb_section_reply("contact", "chat_contact_reply")
        return None

    def _is_skills(self, normalized):
        if any(self._contains_word(normalized, word) for word in ["skills", "technologies", "tech stack", "what do you know", "stack"]):
            self._last_topic = "skills"
            return self._kb_section_reply("skills", "chat_skills_reply")
        return None

    def _is_identity(self, normalized):
        return any(self._contains_word(normalized, word) for word in IDENTITY_PATTERNS)

    def _is_negative(self, normalized):
        return any(self._contains_word(normalized, word) for word in NEGATIVE_PHRASES)

    def _is_joke(self, normalized):
        return any(self._contains_word(normalized, word) for word in JOKE_PATTERNS)

    def _is_redirect(self, normalized):
        if any(self._contains_word(normalized, word) for word in REDIRECT_PHRASES):
            return True
        cleaned = normalized.strip(" ?!.,;:")
        return cleaned in {"what", "huh", "idk", "wat", "wut", "hmm"}

    def _is_qr_question(self, normalized):
        return any(self._contains_word(normalized, word) for word in QR_CODE_PATTERNS)

    def _is_survey_question(self, normalized):
        return any(self._contains_word(normalized, word) for word in SURVEY_LINK_PATTERNS)

    def _survey_url(self):
        mode = ""
        try:
            from flask import request

            mode = request.args.get("mode") or ""
        except Exception:
            pass
        if mode == "professional":
            return SURVEY_URL_PROFESSIONAL
        return SURVEY_URL_DEFAULT

    def _resolve_survey_question(self, normalized):
        if not self._is_survey_question(normalized):
            if not (
                self._contains_word(normalized, "google")
                and any(pattern in normalized for pattern in URL_QUESTION_PATTERNS)
            ):
                return None
        return gettext("chat_survey_reply").format(url=self._survey_url())

    def _url_topic_from_text(self, normalized):
        for topic, keywords in PAGE_TOPIC_KEYWORDS:
            if any(self._contains_word(normalized, keyword) for keyword in keywords):
                return topic
        return None

    def _resolve_url_question(self, normalized):
        if any(self._contains_word(normalized, word) for word in SOCIAL_LINK_WORDS):
            return None
        if not any(pattern in normalized for pattern in URL_QUESTION_PATTERNS):
            return None
        topic = self._url_topic_from_text(normalized)
        if topic is None and self._session_id:
            session = self._sessions.get(self._session_id)
            if session and session.get("last_topic") in PAGE_PATHS:
                topic = session["last_topic"]
        if topic and topic in PAGE_PATHS:
            return gettext("chat_url_reply").format(url=self._site_url(PAGE_PATHS[topic]))
        urls = " • ".join(self._site_url(PAGE_PATHS[topic_key]) for topic_key in PAGE_PATHS)
        return gettext("chat_urls_all").format(urls=urls)

    def _is_girlfriend_question(self, normalized):
        return any(self._contains_word(normalized, word) for word in GIRLFRIEND_PATTERNS)

    def _is_unrelated(self, normalized, expanded):
        text = f"{normalized} {expanded}"
        return any(self._contains_word(text, pattern) for pattern in UNRELATED_PATTERNS)

    def _resolve_girlfriend_contact(self, normalized):
        if not self._is_girlfriend_question(normalized):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_PRIVATE_PATTERNS):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_contact_reply")

    def _resolve_girlfriend_followup_contact(self, normalized):
        if not self._session_id:
            return None
        if not self._girlfriend_session_context():
            return None
        if not any(self._contains_word(normalized, word) for word in ["she", "her"]):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_PRIVATE_PATTERNS):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_contact_reply")

    def _resolve_girlfriend_company(self, normalized):
        if not self._is_girlfriend_question(normalized):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_COMPANY_WORDS):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_company_reply")

    def _resolve_girlfriend_followup_company(self, normalized):
        if not self._session_id:
            return None
        if not self._girlfriend_session_context():
            return None
        if not any(self._contains_word(normalized, word) for word in ["she", "her"]):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_COMPANY_WORDS):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_company_reply")

    def _resolve_girlfriend_age(self, normalized):
        if not self._is_girlfriend_question(normalized):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_AGE_WORDS):
            return None
        self._last_topic = "girlfriend"
        return self._girlfriend_age_reply(normalized)

    def _resolve_girlfriend_followup_age(self, normalized):
        if not self._session_id:
            return None
        if not self._girlfriend_session_context():
            return None
        if not any(self._contains_word(normalized, word) for word in ["she", "her"]):
            return None
        if not any(self._contains_word(normalized, word) for word in GIRLFRIEND_AGE_WORDS):
            return None
        self._last_topic = "girlfriend"
        return self._girlfriend_age_reply(normalized)

    def _girlfriend_age(self):
        today = datetime.now()
        age = today.year - GIRLFRIEND_BIRTHDAY.year
        if (today.month, today.day) < (GIRLFRIEND_BIRTHDAY.month, GIRLFRIEND_BIRTHDAY.day):
            age -= 1
        return age

    def _asked_age(self, normalized):
        match = re.search(r"(\d+)\s*(?:years?\s*old|yrs?\b|year\b)", normalized)
        if match:
            return int(match.group(1))
        if "years old" in normalized or "age" in normalized:
            match = re.search(r"\b(\d+)\b", normalized)
            if match:
                return int(match.group(1))
        return None

    def _girlfriend_age_reply(self, normalized):
        age = self._girlfriend_age()
        asked = self._asked_age(normalized)
        if asked is not None:
            if asked == age:
                return gettext("chat_girlfriend_age_yes_reply").format(age=age)
            return gettext("chat_girlfriend_age_no_reply").format(age=age, asked=asked)
        return gettext("chat_girlfriend_age_reply").format(age=age)

    def _girlfriend_session_context(self):
        if not self._session_id:
            return False
        session = self._sessions.get(self._session_id)
        if not session:
            return False
        if session.get("last_topic") == "girlfriend":
            return True
        for turn in (session.get("turns") or [])[-8:]:
            text = (turn.get("text") or "").lower()
            if "fiona" in text or "girlfriend" in text:
                return True
        return False

    def _resolve_girlfriend(self, normalized):
        if not self._is_girlfriend_question(normalized):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_reply")

    def _resolve_girlfriend_followup(self, normalized):
        if not self._session_id:
            return None
        if not self._girlfriend_session_context():
            return None
        if not any(self._contains_word(normalized, word) for word in ["she", "her"]):
            return None
        self._last_topic = "girlfriend"
        return gettext("chat_girlfriend_reply")

    def _site_base_url(self):
        try:
            from flask import request

            base = request.host_url
            if base:
                return base
        except Exception:
            pass
        return os.getenv("SITE_URL", "")

    def _site_url(self, path=""):
        base = self._site_base_url()
        if not base:
            return path
        base = base.rstrip("/")
        cleaned = (path or "").lstrip("/")
        if not cleaned:
            return base
        return base + "/" + cleaned

    # ------------------------------ ai layer ------------------------------

    def _get_gemini_service(self):
        if self.gemini_service is None:
            from app.Services.GeminiService import GeminiService

            candidate = GeminiService()
            if candidate.is_available():
                self.gemini_service = candidate
        return self.gemini_service

    def _ai_context(self):
        base = self._site_base_url()
        parts = [
            "SITE BASE URL: " + (base or "(use relative paths)"),
            "PAGE LINKS: " + ", ".join(
                f"{key}={self._site_url(path)}" for key, path in PAGE_PATHS.items()
            ),
            f"CONCERN SURVEY LINK: {SURVEY_URL_DEFAULT}"
            f" (professional mode: {SURVEY_URL_PROFESSIONAL})",
            "GIRLFRIEND: Fiona Samantha Escarro is the girlfriend of the site owner.",
            "GIRLFRIEND PERSONALITY: She is an introvert and smart. Her face often looks "
            "angry but she is actually pretty. She is a small girl, and in the site owner's "
            "opinion she is sexy. When asked about her, describe her with these traits "
            "warmly and in detail.",
            "GIRLFRIEND FACTS: Her birthday is 04/11/2005. She lives in Bantayan. "
            "She is one of the PN scholars. She worked as an intern at TrustArc and is "
            "now a non-voice assistant at her current work, Teleperformance in IT Park. "
            "When asked about her company, say she works at Teleperformance in IT Park.",
            "GIRLFRIEND RULES: When asked about her, answer in detail and warmly. "
            "Never reveal her personal contact details such as phone number, email, "
            "address, or social media accounts. If asked about those, say you do not "
            "know about her contacts. If asked further about Teleperformance as a BPO "
            "company, answer in detail.",
        ]
        try:
            locale = get_locale() or "en"
        except Exception:
            locale = "en"
        age = str(self._age())
        dynamic_reply = self._current_company_reply()
        for section in self._knowledge_base().sections():
            loc = (section.get("localized") or {}).get(locale) or {}
            heading = loc.get("heading") or section["heading"]
            body = loc.get("body") or section.get("body")
            if heading in DYNAMIC_KB_QUESTIONS and dynamic_reply:
                body = dynamic_reply
            if heading and body:
                parts.append(f"Q: {heading}\nA: {body.replace('{age}', age)}")
        for topic, fetcher in (
            ("projects", self._fetch_projects),
            ("experience", self._fetch_roadmaps),
            ("gallery", self._fetch_gallery),
            ("vlog", self._fetch_vlog),
            ("music", self._fetch_music),
        ):
            try:
                items, fields = fetcher()
            except Exception:
                continue
            for item in (items or [])[:20]:
                record = self._item_record(topic, item)
                if record.get("detail"):
                    parts.append(f"{topic.upper()}: {record['detail']}")
        try:
            roadmaps, _ = self._fetch_roadmaps()
        except Exception:
            roadmaps = []
        for entry in (roadmaps or [])[:10]:
            company = str(entry.get("company_name") or "").strip()
            if not company:
                continue
            role = self._localize_roadmap_role(entry)
            period = str(entry.get("period") or "").strip()
            location = str(entry.get("location") or "").strip()
            definition = self._localize_text(entry.get("definition"))
            summary = self._localize_text(entry.get("summary"))
            highlights = entry.get("highlights") or []
            parts.append(f"COMPANY: {company}")
            if role:
                parts.append(f"COMPANY ROLE: {role}")
            if period:
                parts.append(f"COMPANY PERIOD: {period}")
            if location:
                parts.append(f"COMPANY LOCATION: {location}")
            if definition:
                parts.append(f"COMPANY DEFINITION: {definition}")
            if summary:
                parts.append(f"COMPANY SUMMARY: {summary}")
            if highlights:
                parts.append(f"COMPANY HIGHLIGHTS: {'; '.join(str(h) for h in highlights)}")
        company_rules = self._company_rules_text(roadmaps)
        if company_rules:
            parts.append(company_rules)
        return "\n".join(parts)

    def _company_rules_text(self, roadmaps):
        entries = [self._as_dict(item) for item in (roadmaps or [])]
        companies = []
        for entry in entries:
            company = str(entry.get("company_name") or "").strip()
            if company and company not in companies:
                companies.append(company)
        current = self._current_roadmap_entry(entries)
        current_name = str(current.get("company_name") or "").strip() if current else ""
        if not companies:
            return "COMPANY RULES: When asked about a company Joshua has worked at, answer in full detail about the company itself."
        lines = [
            "COMPANY RULES: The companies Joshua has worked at are: "
            + ", ".join(companies) + "."
        ]
        if current_name:
            lines.append(f"His current company is {current_name}.")
        lines.append(
            "When the user asks about the COMPANY itself (for example 'your company', "
            f"'what is {current_name or companies[0]} about', 'what does the company "
            "offer', 'what is the purpose'), answer with a full company profile based on "
            "the COMPANY data included in this content: the company name, what it does, "
            "its purpose, the services and offers it provides, where it is located, and "
            "its highlights — mention Joshua's role only briefly. Use the COMPANY data as "
            "the base and your own knowledge of the company for additional detail. Never "
            "contradict the COMPANY data."
        )
        return "\n".join(lines)

    def _ai_history(self, message):
        if not self._session_id:
            return []
        session = self._sessions.get(self._session_id)
        if not session:
            return []
        turns = session.get("turns") or []
        if turns and turns[-1].get("text") == message:
            turns = turns[:-1]
        return [
            {"role": turn.get("role"), "text": turn.get("text")}
            for turn in turns[-6:]
            if turn.get("text")
        ]

    def _ai_chat_answer(self, message):
        gemini = self._get_gemini_service()
        if gemini is None:
            return None
        try:
            context = self._ai_context()
        except Exception:
            context = ""
        try:
            history = self._ai_history(message)
        except Exception:
            history = []
        try:
            return gemini.answer(message, context, history=history)
        except Exception:
            return None

    def _contains_word(self, text, word):
        return re.search(rf"\b{re.escape(word)}\b", text) is not None

    def _contains_phrase(self, text, phrase):
        return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

    # --------------------------- session store ---------------------------

    def _prune_sessions(self):
        now = time.time()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.get("updated_at", 0) > CHAT_SESSION_TTL_SECONDS
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
        if len(self._sessions) > CHAT_SESSION_MAX_COUNT:
            oldest = sorted(
                self._sessions,
                key=lambda sid: self._sessions[sid].get("updated_at", 0),
            )
            for sid in oldest[:len(self._sessions) - CHAT_SESSION_MAX_COUNT]:
                self._sessions.pop(sid, None)

    def _get_session(self, session_id):
        now = time.time()
        session = self._sessions.get(session_id)
        if session is None:
            session = {
                "updated_at": now,
                "last_topic": None,
                "last_item": None,
                "last_items": None,
                "turns": [],
            }
            self._sessions[session_id] = session
        session["updated_at"] = now
        if len(session["turns"]) > CHAT_SESSION_MAX_TURNS:
            session["turns"] = session["turns"][-CHAT_SESSION_MAX_TURNS:]
        return session

    def _remember_user(self, message):
        if not self._session_id:
            return
        session = self._get_session(self._session_id)
        session["turns"].append({"role": "user", "text": message})

    def _remember_turn(self, result):
        if not self._session_id:
            return
        session = self._get_session(self._session_id)
        if self._last_topic is not None:
            session["last_topic"] = self._last_topic
        if self._last_item is not None:
            session["last_item"] = self._last_item
            session["last_items"] = None
        if self._last_reply_items is not None:
            session["last_items"] = self._last_reply_items
            session["last_item"] = None
        session["turns"].append({
            "role": "bot",
            "text": result.get("answer"),
            "matched_question": result.get("matched_question"),
            "topic": self._last_topic,
        })
        self._last_topic = None
        self._last_item = None
        self._last_reply_items = None

    # --------------------------- follow ups ------------------------------

    def _resolve_follow_up(self, normalized, expanded):
        if not self._session_id:
            return None
        session = self._sessions.get(self._session_id)
        if session is None:
            return None
        last_item = session.get("last_item")
        last_items = session.get("last_items") or []
        if not last_item and not last_items:
            return None

        if self._is_follow_up_more(expanded):
            if last_item:
                return self._reply(
                    last_item["detail"],
                    matched_question=last_item["title"],
                )
            return self._follow_up_list_reply(last_items)

        ordinal = self._ordinal_index(expanded)
        if ordinal is not None and last_items:
            if 0 <= ordinal < len(last_items):
                entry = last_items[ordinal]
                self._last_item = entry
                return self._reply(entry["detail"], matched_question=entry["title"])
            return self._reply(
                gettext("chat_followup_range").replace("{count}", str(len(last_items)))
            )

        if self._is_follow_up_which(expanded) and last_items and self._has_item_reference(expanded):
            return self._follow_up_list_reply(last_items)

        return None

    def _follow_up_list_reply(self, last_items):
        shown = [entry["title"] for entry in last_items[:3] if entry.get("title")]
        if not shown:
            return None
        self._last_reply_items = last_items
        answer = f"{gettext('chat_followup_more_intro')} {' • '.join(shown)}"
        return self._reply(answer, action="expand_options")

    def _is_follow_up_more(self, expanded):
        return any(phrase in expanded for phrase in FOLLOW_UP_MORE_PATTERNS)

    def _is_follow_up_which(self, expanded):
        return any(phrase in expanded for phrase in FOLLOW_UP_WHICH_PATTERNS)

    def _ordinal_index(self, expanded):
        for word, index in ORDINAL_WORDS.items():
            if self._contains_word(expanded, word):
                return index
        return None

    def _has_item_reference(self, expanded):
        if self._ordinal_index(expanded) is not None:
            return True
        return any(
            phrase in expanded
            for phrase in ["this one", "that one", "one of", "any of", "them", "these", "those", "this", "that"]
        )

    def _suggest_follow_ups(self, qa):
        if not self._session_id:
            return None
        session = self._sessions.get(self._session_id)
        if session is None:
            return None
        last_item = session.get("last_item")
        last_items = session.get("last_items") or []
        if last_item and last_item.get("title"):
            return f"{gettext('chat_followup_more_intro')} {last_item['title']}"
        if last_items:
            shown = [entry["title"] for entry in last_items[:3] if entry.get("title")]
            if shown:
                return f"{gettext('chat_followup_more_intro')} {' • '.join(shown)}"
        return None

    # --------------------------- content layer ---------------------------

    def _resolve_content(self, normalized, expanded):
        for topic, patterns, method in TOPIC_HANDLERS:
            if any(self._contains_word(normalized, word) for word in patterns):
                return getattr(self, method)(normalized, expanded)
        return None

    def _search_topics_content(self, expanded):
        searches = [
            ("projects", self._fetch_projects),
            ("experience", self._fetch_roadmaps),
            ("gallery", self._fetch_gallery),
            ("vlog", self._fetch_vlog),
            ("music", self._fetch_music),
        ]
        for topic, fetcher in searches:
            try:
                items, fields = fetcher()
            except Exception:
                continue
            if items and self._content_phrase_hit(expanded, topic, items):
                return topic
        for topic, fetcher in searches:
            try:
                items, fields = fetcher()
            except Exception:
                continue
            if items and self._best_content_item(expanded, items, fields):
                return topic
        return None

    def _content_phrase_hit(self, expanded, topic, items):
        for item in items:
            if topic == "experience":
                company = str(item.get("company_name") or "").strip()
                role = self._localize_roadmap_role(item)
                if company and self._contains_word(expanded, self._normalize_spacing(company.lower())):
                    return True
                if role and self._contains_word(expanded, self._normalize_spacing(role.lower())):
                    return True
            elif topic == "music":
                title = str(item.get("title") or "").strip()
                artist = str(item.get("artist") or "").strip()
                if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                    return True
                if artist and self._contains_word(expanded, self._normalize_spacing(artist.lower())):
                    return True
            else:
                title = self._localize_text(item.get("title"))
                if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                    return True
        return False

    def _fetch_projects(self):
        if self.key_project_service is None:
            return [], []
        items = self.key_project_service.get_active_key_projects()
        return [self._as_dict(item) for item in (items or [])], ["title", "description", "stack", "status"]

    def _fetch_roadmaps(self):
        if self.company_roadmap_service is None:
            return [], []
        items = self.company_roadmap_service.get_active_company_roadmaps()
        return [self._as_dict(item) for item in (items or [])], ["company_name", "role_title", "role_title_i18n", "location", "period"]

    def _fetch_gallery(self):
        if self.gallery_service is None:
            return [], []
        items, total = self.gallery_service.search_gallery_paginated(
            "", "", self._locale, 1, 6, SortOrder.DESC
        )
        return [self._as_dict(item) for item in (items or [])], ["title", "description", "tags"]

    def _fetch_vlog(self):
        if self.video_service is None:
            return [], []
        items, total = self.video_service.search_video_paginated(
            "", "", self._locale, 1, 6, SortOrder.DESC
        )
        return [self._as_dict(item) for item in (items or [])], ["title", "description", "tags"]

    def _fetch_music(self):
        if self.music_service is None:
            return [], []
        items, total = self.music_service.get_paginated_music_list(1, 6, SortOrder.DESC, "", "")
        return [self._as_dict(item) for item in (items or [])], ["title", "artist"]

    def _fuzzy_topic_match(self, normalized):
        tokens = self._normalize_tokens(normalized)
        if not tokens:
            return None
        best = None
        best_key = None
        for topic, patterns, method in TOPIC_HANDLERS:
            hits = 0
            max_ratio = 0.0
            for phrase in patterns:
                words = [
                    w for w in re.findall(r"[a-z0-9]+", phrase.lower())
                    if len(w) > 1 and w not in CHAT_STOPWORDS
                ]
                if not words:
                    continue
                ratios = [
                    max(self._fuzzy_ratio(word, [tok]) for tok in tokens)
                    for word in words
                ]
                if all(ratio >= CHAT_FUZZY_WORD_RATIO for ratio in ratios):
                    hits = max(hits, len(words))
                    max_ratio = max(max_ratio, max(ratios))
            key = (hits, max_ratio)
            if hits >= 1 and (best_key is None or key > best_key):
                best_key = key
                best = (topic, patterns, method)
        return best

    def _content_blob(self, item, fields):
        parts = []
        for field in fields:
            value = item.get(field)
            if isinstance(value, dict):
                value = self._localize_text(value)
            if isinstance(value, list):
                parts.extend(str(x) for x in value)
            else:
                parts.append(str(value or ""))
        return " ".join(parts).lower()

    def _content_score(self, text, tokens, blob_text):
        blob_tokens = self._normalize_tokens(blob_text)
        overlap = self._token_overlap(tokens, blob_tokens)
        bigram = self._bigram_similarity(text, blob_text)
        blob_set = set(blob_tokens)
        common = sum(1 for word in tokens if word in blob_set)
        distinct = len(set(tokens) & blob_set)
        coverage = (common / len(tokens)) if tokens else 0
        return {"overlap": overlap, "bigram": bigram, "distinct": distinct, "coverage": coverage}

    def _content_is_match(self, score):
        if not score or score["distinct"] < 2:
            return False
        return score["coverage"] >= CHAT_COVERAGE_THRESHOLD

    def _best_content_item(self, text, items, fields):
        tokens = self._normalize_tokens(text)
        if not tokens:
            return None
        scored = []
        for item in items:
            blob_text = self._content_blob(item, fields)
            score = self._content_score(text, tokens, blob_text)
            if not score["distinct"]:
                continue
            rank = score["overlap"] + 0.3 * score["bigram"]
            scored.append((rank, score, item))
        if not scored:
            return None
        scored.sort(key=lambda entry: entry[0], reverse=True)
        rank, score, item = scored[0]
        if self._content_is_match(score):
            return item
        return None

    def _item_record(self, topic, item):
        if topic == "projects":
            title = self._localize_text(item.get("title"))
            return {"title": title, "detail": self._project_detail(item, title)}
        if topic == "experience":
            role = self._localize_roadmap_role(item)
            company = str(item.get("company_name") or "").strip()
            period = str(item.get("period") or "").strip()
            if company and period:
                detail = f"{role} @ {company} ({period})"
            elif company:
                detail = f"{role} @ {company}"
            else:
                detail = role
            return {"title": company or role, "detail": detail}
        if topic == "music":
            title = str(item.get("title") or "").strip()
            artist = str(item.get("artist") or "").strip()
            if title and artist:
                detail = f"{title} - {artist}"
            else:
                detail = title or artist
            return {"title": title or artist, "detail": detail}
        title = self._localize_text(item.get("title"))
        description = self._localize_text(item.get("description"))
        detail = title
        if description:
            detail += f" — {description}"
        return {"title": title, "detail": detail}

    def _topic_item_reply(self, record, topic):
        self._last_item = record
        return self._reply(record["detail"], matched_question=record["title"])

    def _topic_summary(self, normalized, expanded):
        self._last_topic = "summary"
        return self._reply(self._kb_section_reply("summary", "chat_summary_reply"))

    def _topic_about(self, normalized, expanded):
        self._last_topic = "about"
        return self._reply(self._kb_section_reply("about", "chat_about_reply"))

    def _topic_projects(self, normalized, expanded):
        self._last_topic = "projects"
        kb = self._kb_match(expanded)
        if kb:
            return kb
        service = self.key_project_service
        if service is None:
            return self._reply(gettext("chat_content_unavailable"))
        try:
            items = service.get_active_key_projects()
        except Exception:
            return self._reply(gettext("chat_content_unavailable"))
        projects = [self._as_dict(item) for item in (items or [])]
        if not projects:
            return self._reply(gettext("chat_content_empty"))

        for project in projects:
            title = self._localize_text(project.get("title"))
            if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                return self._topic_item_reply(self._item_record("projects", project), "projects")

        best = self._best_content_item(
            expanded, projects, ["title", "description", "stack", "status"]
        )
        if best:
            return self._topic_item_reply(self._item_record("projects", best), "projects")

        titles = [self._localize_text(p.get("title")) for p in projects]
        titles = [t for t in titles if t]
        shown, total = self._cap_list(titles)
        self._last_reply_items = [self._item_record("projects", p) for p in projects[:6]]
        answer = f"{gettext('chat_projects_intro')} {' • '.join(shown)}"
        if total > len(shown):
            answer += self._count_suffix(total)
        return self._reply(answer)

    def _topic_experience(self, normalized, expanded):
        self._last_topic = "experience"
        kb = self._kb_match(expanded)
        if kb:
            return kb
        service = self.company_roadmap_service
        if service is None:
            return self._reply(gettext("chat_content_unavailable"))
        try:
            items = service.get_active_company_roadmaps()
        except Exception:
            return self._reply(gettext("chat_content_unavailable"))
        entries = [self._as_dict(item) for item in (items or [])]
        if not entries:
            return self._reply(gettext("chat_content_empty"))

        for entry in entries:
            company = str(entry.get("company_name") or "").strip()
            if company and self._contains_word(expanded, self._normalize_spacing(company.lower())):
                return self._topic_item_reply(self._item_record("experience", entry), "experience")

        best = self._best_content_item(
            expanded, entries,
            ["company_name", "role_title", "role_title_i18n", "location", "period"],
        )
        if best:
            return self._topic_item_reply(self._item_record("experience", best), "experience")

        roles = []
        for entry in entries:
            record = self._item_record("experience", entry)
            if record["detail"]:
                roles.append(record["detail"])
        roles = [r for r in roles if r]
        shown, total = self._cap_list(roles)
        self._last_reply_items = [self._item_record("experience", e) for e in entries[:6]]
        answer = f"{gettext('chat_experience_intro')} {' • '.join(shown)}"
        if total > len(shown):
            answer += self._count_suffix(total)
        return self._reply(answer)

    def _topic_certifications(self, normalized, expanded):
        self._last_topic = "certifications"
        return self._reply(self._kb_section_reply("certifications", "chat_certifications_reply"))

    def _topic_education(self, normalized, expanded):
        self._last_topic = "education"
        return self._reply(self._kb_section_reply("education", "chat_education_reply"))

    def _topic_gallery(self, normalized, expanded):
        self._last_topic = "gallery"
        kb = self._kb_match(expanded)
        if kb:
            return kb
        service = self.gallery_service
        if service is None:
            return self._reply(gettext("chat_content_unavailable"))
        try:
            items, total = service.search_gallery_paginated(
                "", "", self._locale, 1, 6, SortOrder.DESC
            )
        except Exception:
            return self._reply(gettext("chat_content_unavailable"))
        if self._is_count_question(expanded):
            return self._reply(gettext("chat_gallery_count_reply").format(total=total))
        items = [self._as_dict(item) for item in (items or [])]
        if not items:
            return self._reply(gettext("chat_content_empty"))

        for item in items:
            title = self._localize_text(item.get("title"))
            if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                return self._topic_item_reply(self._item_record("gallery", item), "gallery")

        best = self._best_content_item(expanded, items, ["title", "description", "tags"])
        if best:
            return self._topic_item_reply(self._item_record("gallery", best), "gallery")

        titles = [self._localize_text(item.get("title")) for item in items]
        titles = [t for t in titles if t]
        shown, total = self._cap_list(titles, total)
        self._last_reply_items = [self._item_record("gallery", item) for item in items[:6]]
        answer = f"{gettext('chat_gallery_intro')} {' • '.join(shown)}"
        if total > len(shown):
            answer += self._count_suffix(total)
        return self._reply(answer)

    def _topic_vlog(self, normalized, expanded):
        self._last_topic = "vlog"
        kb = self._kb_match(expanded)
        if kb:
            return kb
        service = self.video_service
        if service is None:
            return self._reply(gettext("chat_content_unavailable"))
        try:
            items, total = service.search_video_paginated(
                "", "", self._locale, 1, 6, SortOrder.DESC
            )
        except Exception:
            return self._reply(gettext("chat_content_unavailable"))
        if self._is_count_question(expanded):
            return self._reply(gettext("chat_vlog_count_reply").format(total=total))
        items = [self._as_dict(item) for item in (items or [])]
        if not items:
            return self._reply(gettext("chat_content_empty"))

        for item in items:
            title = self._localize_text(item.get("title"))
            if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                return self._topic_item_reply(self._item_record("vlog", item), "vlog")

        best = self._best_content_item(expanded, items, ["title", "description", "tags"])
        if best:
            return self._topic_item_reply(self._item_record("vlog", best), "vlog")

        titles = [self._localize_text(item.get("title")) for item in items]
        titles = [t for t in titles if t]
        shown, total = self._cap_list(titles, total)
        self._last_reply_items = [self._item_record("vlog", item) for item in items[:6]]
        answer = f"{gettext('chat_vlog_intro')} {' • '.join(shown)}"
        if total > len(shown):
            answer += self._count_suffix(total)
        return self._reply(answer)

    def _topic_music(self, normalized, expanded):
        self._last_topic = "music"
        kb = self._kb_match(expanded)
        if kb:
            return kb
        service = self.music_service
        if service is None:
            return self._reply(gettext("chat_content_unavailable"))
        try:
            items, total = service.get_paginated_music_list(1, 6, SortOrder.DESC, "", "")
        except Exception:
            return self._reply(gettext("chat_content_unavailable"))
        if self._is_count_question(expanded):
            return self._reply(gettext("chat_music_count_reply").format(total=total))
        items = [self._as_dict(item) for item in (items or [])]
        if not items:
            return self._reply(gettext("chat_content_empty"))

        for item in items:
            title = str(item.get("title") or "").strip()
            artist = str(item.get("artist") or "").strip()
            if title and self._contains_word(expanded, self._normalize_spacing(title.lower())):
                return self._topic_item_reply(self._item_record("music", item), "music")
            if artist and self._contains_word(expanded, self._normalize_spacing(artist.lower())):
                return self._topic_item_reply(self._item_record("music", item), "music")

        best = self._best_content_item(expanded, items, ["title", "artist"])
        if best:
            return self._topic_item_reply(self._item_record("music", best), "music")

        songs = []
        for item in items:
            record = self._item_record("music", item)
            if record["detail"]:
                songs.append(record["detail"])
        shown, total = self._cap_list(songs, total)
        self._last_reply_items = [self._item_record("music", item) for item in items[:6]]
        answer = f"{gettext('chat_music_intro')} {' • '.join(shown)}"
        if total > len(shown):
            answer += self._count_suffix(total)
        return self._reply(answer)

    def _topic_donation(self, normalized, expanded):
        self._last_topic = "donation"
        return self._reply(self._kb_section_reply("donation", "chat_donation_reply"))

    def _topic_booking(self, normalized, expanded):
        self._last_topic = "booking"
        return self._reply(self._kb_section_reply("booking", "chat_booking_reply"))

    def _topic_concern(self, normalized, expanded):
        self._last_topic = "concern"
        return self._reply(self._kb_section_reply("concern", "chat_concern_reply"))

    def _project_detail(self, project, title=None):
        title = title or self._localize_text(project.get("title"))
        description = self._localize_text(project.get("description"))
        stack = str(project.get("stack") or "").strip()
        status = str(project.get("status") or "").strip()
        parts = [title]
        if description:
            parts.append(description)
        if stack:
            parts.append(f"[{stack}]")
        if status:
            parts.append(f"[{status}]")
        return " — ".join(parts)

    # ----------------------------- helpers -------------------------------

    def _as_dict(self, item):
        if hasattr(item, "to_dict"):
            return item.to_dict()
        return dict(item or {})

    def _localize_text(self, value):
        if isinstance(value, dict):
            return str(value.get(self._locale) or value.get("en") or "").strip()
        return str(value or "").strip()

    def _localize_roadmap_role(self, entry):
        i18n = entry.get("role_title_i18n") or {}
        role = self._localize_text(i18n)
        if not role:
            role = str(entry.get("role_title") or "").strip()
        return role

    def _cap_list(self, items, total=None):
        items = list(items)
        return items[:6], max(total or len(items), len(items))

    def _count_suffix(self, total):
        return gettext("chat_content_more").replace("{count}", str(total - 6))

    # --------------------------- QA matching -----------------------------

    def _expand_message(self, text):
        result = (text or "").lower()
        for source, target in sorted(CONTRACTIONS.items(), key=lambda kv: -len(kv[0])):
            result = re.sub(rf"\b{re.escape(source)}\b", target, result)
        return result

    def _normalize_spacing(self, text):
        result = re.sub(r"[\-_·•/]+", " ", (text or "").lower())
        return re.sub(r"\s+", " ", result).strip()

    def _strip_noise(self, text):
        result = (text or "").strip()
        changed = True
        while changed:
            changed = False
            for phrase in NOISE_PREFIXES:
                if result == phrase or result.startswith(phrase + " "):
                    result = result[len(phrase):].strip(" ,?!.:;")
                    changed = True
        return result

    def _get_exact_answer(self, message, qa_data):
        for item in qa_data:
            if item["question"] == message:
                return self._apply_age(self._kb_answer_for(item))
        return None

    def _apply_age(self, answer):
        return answer.replace("{age}", str(self._age()))

    def _age(self):
        today = datetime.now()
        birth = datetime(2001, 9, 16)
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return age

    def _normalize_tokens(self, text):
        cleaned = re.sub(r"[^a-z0-9\u00e0-\u024f\s]", " ", (text or "").lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return []
        return [
            self._stem_word(word)
            for word in cleaned.split(" ")
            if len(word) > 1 and word not in CHAT_STOPWORDS
        ]

    def _stem_word(self, word):
        if len(word) <= 3:
            return word
        if word.endswith("ies"):
            return word[:-3] + "y"
        if word.endswith("ing") and len(word) > 5:
            return word[:-3]
        if word.endswith("es") and len(word) > 3:
            return word[:-2]
        if word.endswith("ed") and len(word) > 3:
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            return word[:-1]
        return word

    def _levenshtein(self, a, b):
        m, n = len(a), len(b)
        if not m:
            return n
        if not n:
            return m
        prev = list(range(n + 1))
        for i in range(1, m + 1):
            curr = [i]
            for j in range(1, n + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
            prev = curr
        return prev[n]

    def _token_overlap(self, a, b):
        if not a or not b:
            return 0
        set_a = set(a)
        common = sum(1 for word in b if word in set_a)
        return (2 * common) / (len(a) + len(b))

    def _bigram_similarity(self, a, b):
        def grams(s):
            t = re.sub(r"\s+", "", (s or "").lower())
            return [t[i:i + 2] for i in range(len(t) - 1)]

        ga = grams(a)
        gb = grams(b)
        if not ga or not gb:
            return 0
        set_a = set(ga)
        common = sum(1 for g in gb if g in set_a)
        return (2 * common) / (len(ga) + len(gb))

    def _fuzzy_ratio(self, word, tokens):
        if not word or not tokens:
            return 0
        best = 0
        for token in tokens:
            max_len = max(len(word), len(token))
            if not max_len:
                continue
            ratio = 1 - self._levenshtein(word, token) / max_len
            best = max(best, ratio)
        return best

    def _score_qa(self, text, item):
        raw_lower = (text or "").lower()
        match_text = self._strip_noise(raw_lower)
        tokens = self._normalize_tokens(match_text)
        q_text = item.get("question") or ""
        q_tokens = self._normalize_tokens(q_text)
        score = 0.35 * self._token_overlap(tokens, q_tokens)
        score += 0.15 * self._bigram_similarity(match_text, q_text)
        if tokens:
            fuzzy_total = sum(self._fuzzy_ratio(word, q_tokens) for word in tokens)
            score += 0.15 * (fuzzy_total / len(tokens))
        aliases = self._collect_aliases(item)
        if any(self._contains_phrase(raw_lower, alias) for alias in aliases):
            score += 0.4
            return score
        for alias in aliases:
            alias_tokens = self._normalize_tokens(alias)
            if len(alias_tokens) < 2 or len(alias_tokens) > len(tokens):
                continue
            if all(self._fuzzy_ratio(word, tokens) >= CHAT_FUZZY_WORD_RATIO for word in alias_tokens):
                score += 0.4
                break
        return score

    def _find_best_qa(self, text, qa_data):
        best_qa = None
        best_score = 0
        for item in qa_data:
            score = self._score_qa(text, item)
            if score > best_score:
                best_score = score
                best_qa = item
        if best_score >= CHAT_SUGGEST_THRESHOLD and best_qa:
            return {"qa": best_qa, "score": best_score}
        return None

    def _suggest_questions(self, text, qa_data, limit=3):
        scored = []
        for item in qa_data:
            score = self._score_qa(text, item)
            if score >= CHAT_SUGGEST_THRESHOLD:
                scored.append((score, item["question"]))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [question for _, question in scored[:limit]]
