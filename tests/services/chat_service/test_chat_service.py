import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.Services.ChatService import ChatService
from app.Services.KnowledgeBaseService import KnowledgeBaseService


GIRLFRIEND_BIRTHDAY = datetime(2005, 4, 11)


def _girlfriend_age():
    today = datetime.now()
    age = today.year - GIRLFRIEND_BIRTHDAY.year
    if (today.month, today.day) < (GIRLFRIEND_BIRTHDAY.month, GIRLFRIEND_BIRTHDAY.day):
        age -= 1
    return age


def _fake_gettext(key):
    return {
        "chat_greeting_fallback": "Hi! Welcome to my portfolio chat. You can ask me something directly or use the quick questions below.",
        "chat_unknown_fallback": "I can answer the suggested questions below. Try selecting one of the quick options.",
        "chat_unknown_fallback_intro": "I couldn't find anything about that.",
        "chat_quick_questions_intro": "Here are the things I can answer:",
        "chat_sensitive_refusal": "I can't share sensitive or private information like passwords or credentials.",
        "chat_farewell_reply": "Goodbye! Thanks for stopping by.",
        "chat_appreciation_reply": "You're welcome! I'm glad I could help.",
        "chat_how_are_you_reply": "I'm doing great, thanks for asking!",
        "chat_contact_reply": "You can reach me at algadipej962@gmail.com.",
        "chat_skills_reply": "I work with Python, React, and Flask.",
        "chat_identity_reply": "I'm the portfolio chat assistant, a rule-based bot.",
        "chat_negative_reply": "I'm sorry to hear that!",
        "chat_joke_reply": "Why do programmers prefer dark mode?",
        "chat_redirect_reply": "Try rephrasing, or pick a suggested question.",
        "chat_did_you_mean": "Did you mean one of these?",
        "chat_developers_reply": "Made by me with J-AlDev and Brocode Devs.",
        "chat_certifications_reply": "Certs: Angular, Java, SQL, Flask.",
        "chat_education_reply": "Education: TrustArc and Chronostep.",
        "chat_summary_reply": "5+ years, 12+ projects, 8 certifications.",
        "chat_about_reply": "I am a passionate software developer.",
        "chat_donation_reply": "Donate via GCash on the Donation page.",
        "chat_booking_reply": "Book: Website Development, Web Apps, and more.",
        "chat_concern_reply": "Share feedback on the Concern page.",
        "chat_qr_reply": "The donation QR codes are on the Donation page — open {url} to scan the code and send your gift.",
        "chat_url_reply": "Here's the link: {url}",
        "chat_urls_all": "Here are the main pages: {urls}",
        "chat_survey_reply": "Here's the survey link: {url}",
        "chat_projects_intro": "Key projects:",
        "chat_experience_intro": "Experience:",
        "chat_gallery_intro": "Gallery photos:",
        "chat_vlog_intro": "Recent vlogs:",
        "chat_music_intro": "Songs:",
        "chat_content_empty": "No items found for that topic.",
        "chat_content_unavailable": "That info is unavailable right now.",
        "chat_content_more": " ... and {count} more.",
        "chat_followup_more_intro": "I can tell you more about these:",
        "chat_followup_range": "I only have {count} items there.",
        "chat_gallery_count_reply": "I have {total} photos in my gallery.",
        "chat_vlog_count_reply": "I have {total} vlogs in my collection.",
        "chat_music_count_reply": "I have {total} songs in my collection.",
        "chat_current_role_reply": "I am currently working as a {role} at {company}.",
        "chat_girlfriend_reply": "Fiona Samantha Escarro.",
        "chat_girlfriend_contact_reply": "I don't know about her contacts.",
        "chat_girlfriend_company_reply": "She works at Teleperformance in IT Park.",
        "chat_girlfriend_age_reply": "Fiona is {age} years old. Her birthday is April 11, 2005.",
        "chat_girlfriend_age_yes_reply": "Yes, she is {age} years old! Fiona was born on April 11, 2005.",
        "chat_girlfriend_age_no_reply": "No, she is {age} years old, not {asked}. Fiona was born on April 11, 2005.",
        "chat_unrelated_reply": "That question is unrelated to my conversation. Please focus on my skills, projects, experience, and everything on this site!",
    }.get(key, key)


def _make_service(method, result):
    service = MagicMock()
    getattr(service, method).return_value = result
    return service


def _localized_gettext_factory(replies):
    def _gettext(key):
        if key in replies:
            return replies[key]
        return _fake_gettext(key)
    return _gettext


QA = [
    {"question": "What is your name?", "answer": "My name is Joshua P. Algadipe."},
    {"question": "What is your age?", "answer": "I am {age} years old."},
    {"question": "What do you call yourself?", "answer": "You can call me JJ, Josh, or Wang."},
    {"question": "What is your job?", "answer": "I am a Software Engineer."},
    {"question": "What is your favorite sport?", "answer": "I enjoy basketball."},
    {"question": "What is your favorite subject?", "answer": "My favorite subject is Math."},
    {"question": "Where do you live?", "answer": "I live in Cabulihan, Vallehermoso, Negros Oriental."},
    {"question": "What is your dream job?", "answer": "Primarily my dream job is Electrical Engineering."},
    {"question": "What type of person are you?", "answer": "I'm a bit enigmatic."},
    {"question": "What is your favorite programming language?", "answer": "My favorite programming language is Python."},
]


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return self.service.resolve(message, QA)

    def test_exact_match_returns_answer(self):
        result = self._resolve("What is your name?")
        self.assertEqual(result["answer"], "My name is Joshua P. Algadipe.")
        self.assertIsNone(result["action"])
        self.assertEqual(result["matched_question"], "What is your name?")

    def test_rephrase_route_age(self):
        result = self._resolve("how old are you?")
        self.assertIn("years old", result["answer"])

    def test_typo_route_location(self):
        result = self._resolve("whre do u live?")
        self.assertIn("Cabulihan", result["answer"])

    def test_alias_route_home(self):
        result = self._resolve("where are you from")
        self.assertIn("Cabulihan", result["answer"])

    def test_alias_route_job(self):
        result = self._resolve("what do you do for a living?")
        self.assertIn("Software Engineer", result["answer"])

    def test_alias_route_language(self):
        result = self._resolve("do you like coding?")
        self.assertIn("Python", result["answer"])

    def test_greeting_returns_fallback(self):
        result = self._resolve("hello there!")
        self.assertIn("Welcome to my portfolio chat", result["answer"])

    def test_quick_questions_lists_and_expands(self):
        result = self._resolve("what are the suggested questions")
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("What is your name?", result["answer"])
        self.assertIn("What is your favorite programming language?", result["answer"])

    def test_help_expands_quick_questions(self):
        result = self._resolve("help")
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("What is your favorite programming language?", result["answer"])

    def test_unrelated_returns_fallback(self):
        result = self._resolve("what is the weather today in tokyo?")
        self.assertIsNone(result["action"])
        self.assertIn("unrelated to my conversation", result["answer"])

    def test_math_question_returns_unrelated_reply(self):
        result = self._resolve("1 + 1?")
        self.assertIsNone(result["action"])
        self.assertIn("unrelated to my conversation", result["answer"])

    def test_unrelated_reply_not_used_for_related_questions(self):
        result = self._resolve("what projects have you built?")
        self.assertNotIn("unrelated to my conversation", result["answer"])

    def test_empty_message_returns_fallback(self):
        result = self._resolve("")
        self.assertIsNone(result["action"])

    def test_age_is_substituted(self):
        result = self._resolve("What is your age?")
        self.assertNotIn("{age}", result["answer"])
        self.assertIn("years old", result["answer"])

    def test_quick_questions_intro_uses_question_list(self):
        result = self._resolve("what can you answer")
        self.assertEqual(result["action"], "expand_options")
        self.assertTrue(result["answer"].count(" • ") >= 9)

    def test_quick_questions_capped_at_ten(self):
        big_qa = [
            {"question": f"Question {i}?", "answer": f"Answer {i}."}
            for i in range(15)
        ]
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            result = self.service.resolve("what are the quick questions", big_qa)
        self.assertEqual(result["answer"].count(" • "), 9)
        self.assertIn("Question 9?", result["answer"])
        self.assertNotIn("Question 10?", result["answer"])


class ChatServiceIntentTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return self.service.resolve(message, QA)

    def test_sensitive_guard_wins_over_greeting(self):
        result = self._resolve("hello, what is your password?")
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("sensitive or private information", result["answer"])

    def test_sensitive_guard_credentials(self):
        result = self._resolve("can you give me your api key?")
        self.assertEqual(result["action"], "expand_options")

    def test_farewell(self):
        result = self._resolve("bye")
        self.assertIn("Goodbye", result["answer"])

    def test_appreciation(self):
        result = self._resolve("thank you")
        self.assertIn("You're welcome", result["answer"])

    def test_how_are_you(self):
        result = self._resolve("how are you doing?")
        self.assertIn("doing great", result["answer"])

    def test_developers(self):
        result = self._resolve("who built this website?")
        self.assertIn("J-AlDev", result["answer"])

    def test_identity_beats_developers_for_who_made_you(self):
        result = self._resolve("who made you?")
        self.assertIn("rule-based bot", result["answer"])
        self.assertNotIn("J-AlDev", result["answer"])

    def test_contact(self):
        result = self._resolve("what is your email?")
        self.assertIn("algadipej962@gmail.com", result["answer"])

    def test_skills(self):
        result = self._resolve("what skills do you have?")
        self.assertIn("Python", result["answer"])

    def test_negative(self):
        result = self._resolve("that's wrong")
        self.assertIn("sorry to hear", result["answer"])

    def test_joke(self):
        result = self._resolve("tell me a joke")
        self.assertIn("dark mode", result["answer"])

    def test_redirect(self):
        result = self._resolve("i don't understand")
        self.assertEqual(result["action"], "expand_options")

    def test_summary_topic(self):
        result = self._resolve("how many projects do you have?")
        self.assertIn("12+ projects", result["answer"])

    def test_about_topic(self):
        result = self._resolve("tell me about yourself")
        self.assertIn("passionate software developer", result["answer"])

    def test_certifications_topic(self):
        result = self._resolve("what certifications do you have?")
        self.assertIn("Angular", result["answer"])

    def test_education_topic(self):
        result = self._resolve("where did you study?")
        self.assertIn("TrustArc", result["answer"])

    def test_donation_topic(self):
        result = self._resolve("how can I donate?")
        self.assertIn("GCash", result["answer"])

    def test_booking_topic(self):
        result = self._resolve("I want to book a website")
        self.assertIn("Website Development", result["answer"])

    def test_concern_topic(self):
        result = self._resolve("give feedback")
        self.assertIn("Concern page", result["answer"])

    def test_qr_question_returns_donation_reply(self):
        result = self._resolve("do you have qr code for this?")
        self.assertIn("/donation", result["answer"])
        self.assertNotIn("Python", result["answer"])

    def test_qr_question_without_donation_context(self):
        result = self._resolve("where is the qr code?")
        self.assertIn("Donation", result["answer"])

    def test_url_question_with_page(self):
        result = self._resolve("what is the url of the donation page?")
        self.assertIn("/donation", result["answer"])

    def test_url_reply_uses_site_base_url(self):
        with patch.dict("os.environ", {"SITE_URL": "https://example.com"}):
            result = self._resolve("what is the url of the donation page")
        self.assertIn("https://example.com/donation", result["answer"])

    def test_url_question_gallery(self):
        result = self._resolve("give me the link to the gallery")
        self.assertIn("/gallery", result["answer"])

    def test_url_question_build_page(self):
        result = self._resolve("what is the url of the booking page?")
        self.assertIn("/build", result["answer"])

    def test_url_question_uses_last_topic(self):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            self.service.resolve("how can I donate?", QA, session_id="url-test-1")
            result = self.service.resolve("what is the url?", QA, session_id="url-test-1")
        self.assertIn("/donation", result["answer"])

    def test_url_question_without_topic_lists_pages(self):
        result = self._resolve("what is the url?")
        self.assertIn("/portfolio", result["answer"])
        self.assertIn("/gallery", result["answer"])

    def test_social_link_question_still_uses_contact(self):
        result = self._resolve("what is the link to your facebook?")
        self.assertIn("algadipej962@gmail.com", result["answer"])

    def test_girlfriend_question_replies_name(self):
        result = self._resolve("do you have a girlfriend?")
        self.assertEqual(result["answer"], "Fiona Samantha Escarro.")

    def test_girlfriend_alias_replies_name(self):
        result = self._resolve("who is fiona?")
        self.assertEqual(result["answer"], "Fiona Samantha Escarro.")

    def test_girlfriend_contact_question_refuses(self):
        result = self._resolve("what is your girlfriend's contact number?")
        self.assertEqual(result["answer"], "I don't know about her contacts.")

    def test_girlfriend_email_question_refuses(self):
        result = self._resolve("can i have fiona's email address?")
        self.assertEqual(result["answer"], "I don't know about her contacts.")

    def test_girlfriend_contact_question_beats_contact_intent(self):
        result = self._resolve("what is fiona's facebook?")
        self.assertEqual(result["answer"], "I don't know about her contacts.")
        self.assertNotIn("algadipej962@gmail.com", result["answer"])

    def test_girlfriend_company_question_replies_teleperformance(self):
        result = self._resolve("what company does your girlfriend work at?")
        self.assertEqual(result["answer"], "She works at Teleperformance in IT Park.")

    def test_girlfriend_company_question_beats_ai(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        service = ChatService(gemini_service=gemini)
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            result = service.resolve("what company does fiona work for?", QA)
        self.assertEqual(result["answer"], "She works at Teleperformance in IT Park.")
        gemini.answer.assert_not_called()

    def test_survey_link_question_returns_google_form(self):
        result = self._resolve("tell me the survey link")
        self.assertIn("https://forms.gle/QV5kHc3STEFDFUYf9", result["answer"])

    def test_take_survey_button_link(self):
        result = self._resolve("no the link when i click the take the survey button")
        self.assertIn("https://forms.gle/QV5kHc3STEFDFUYf9", result["answer"])

    def test_concern_link_to_google_returns_survey_form(self):
        result = self._resolve("tell me link of your concern connecting to google")
        self.assertIn("https://forms.gle/QV5kHc3STEFDFUYf9", result["answer"])

    def test_survey_link_professional_mode(self):
        import flask

        fake_request = MagicMock()
        fake_request.args.get.return_value = "professional"
        with patch.object(flask, "request", fake_request):
            result = self._resolve("what is the survey link")
        self.assertIn("https://forms.gle/5UqVgzzxgkJS11Qj9", result["answer"])


class ChatServiceAiTests(unittest.TestCase):
    def _resolve(self, message, gemini=None):
        service = ChatService(gemini_service=gemini)
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message, QA)

    def test_ai_answers_when_rules_cannot_match(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI generated answer."
        result = self._resolve("what are joshua's pets?", gemini=gemini)
        self.assertEqual(result["answer"], "AI generated answer.")
        gemini.answer.assert_called_once()

    def test_ai_unrelated_falls_back(self):
        gemini = MagicMock()
        gemini.answer.return_value = None
        result = self._resolve("what is the meaning of life?", gemini=gemini)
        self.assertIn("couldn't find anything", result["answer"])
        gemini.answer.assert_called_once()

    def test_ai_not_called_for_unrelated_math(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        result = self._resolve("what is 1 + 1?", gemini=gemini)
        self.assertIn("unrelated to my conversation", result["answer"])
        gemini.answer.assert_not_called()

    def test_ai_answers_first_even_for_rule_match(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        result = self._resolve("What is your name?", gemini=gemini)
        self.assertEqual(result["answer"], "AI answer.")
        gemini.answer.assert_called_once()

    def test_ai_answers_backend_language_question(self):
        gemini = MagicMock()
        gemini.answer.return_value = "Backend: Python, PHP (Laravel), and SQL."
        result = self._resolve("what is your backend programming language use", gemini=gemini)
        self.assertEqual(result["answer"], "Backend: Python, PHP (Laravel), and SQL.")
        gemini.answer.assert_called_once()

    def test_ai_context_has_no_age_placeholder(self):
        service = ChatService()
        context = service._ai_context()
        self.assertNotIn("{age}", context)

    def test_ai_context_includes_page_links_and_base_url(self):
        service = ChatService()
        context = service._ai_context()
        self.assertIn("SITE BASE URL:", context)
        self.assertIn("PAGE LINKS:", context)
        self.assertIn("/donation", context)

    def test_no_ai_without_gemini(self):
        result = self._resolve("what are joshua's pets?")
        self.assertIn("couldn't find anything", result["answer"])

    def test_ai_answers_girlfriend_question_in_detail(self):
        gemini = MagicMock()
        gemini.answer.return_value = "Fiona Samantha Escarro is a wonderful person who loves traveling and trying new food."
        result = self._resolve("tell me about your girlfriend", gemini=gemini)
        self.assertEqual(result["answer"], "Fiona Samantha Escarro is a wonderful person who loves traveling and trying new food.")
        gemini.answer.assert_called_once()

    def test_girlfriend_contact_refusal_beats_ai(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        result = self._resolve("what is your girlfriend's contact number?", gemini=gemini)
        self.assertEqual(result["answer"], "I don't know about her contacts.")
        gemini.answer.assert_not_called()

    def test_girlfriend_age_question_beats_ai(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        result = self._resolve("how old is fiona?", gemini=gemini)
        self.assertEqual(result["answer"], f"Fiona is {_girlfriend_age()} years old. Her birthday is April 11, 2005.")
        gemini.answer.assert_not_called()

    def test_girlfriend_age_confirmation_beats_ai(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        age = _girlfriend_age()
        result = self._resolve(f"is fiona {age} years old today", gemini=gemini)
        self.assertEqual(result["answer"], f"Yes, she is {age} years old! Fiona was born on April 11, 2005.")
        gemini.answer.assert_not_called()

    def test_ai_context_includes_girlfriend_info(self):
        service = ChatService()
        context = service._ai_context()
        self.assertIn("Fiona Samantha Escarro", context)
        self.assertIn("GIRLFRIEND RULES", context)

    def test_ai_context_includes_girlfriend_personality(self):
        service = ChatService()
        context = service._ai_context()
        self.assertIn("introvert", context)
        self.assertIn("angry", context)
        self.assertIn("sexy", context)

    def test_ai_context_includes_girlfriend_facts(self):
        service = ChatService()
        context = service._ai_context()
        self.assertIn("04/11/2005", context)
        self.assertIn("Bantayan", context)
        self.assertIn("PN scholars", context)
        self.assertIn("TrustArc", context)
        self.assertIn("non-voice assistant", context)
        self.assertIn("Teleperformance in IT Park", context)

    def test_ai_context_includes_company_rules(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2021 - 2022", "role_title": "Intern", "role_title_i18n": None},
            {"company_name": "Chronostep", "period": "2024 - Present", "role_title": "Software Engineer", "role_title_i18n": None},
        ]
        service = ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))
        context = service._ai_context()
        self.assertIn("COMPANY RULES", context)
        self.assertIn("Chronostep", context)
        self.assertIn("TrustArc", context)
        self.assertIn("full company profile", context)
        self.assertIn("services and offers", context)
        self.assertIn("mention Joshua's role only briefly", context)
        self.assertIn("His current company is Chronostep.", context)

    def test_ai_context_company_rules_follow_current_roadmap(self):
        roadmaps = [
            {"company_name": "Chronostep", "period": "2024 - 2025", "role_title": "Software Engineer", "role_title_i18n": None, "sort_order": 1},
            {"company_name": "FutureCo", "period": "2025 - Present", "role_title": "Senior Engineer", "role_title_i18n": None, "sort_order": 2},
        ]
        service = ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))
        context = service._ai_context()
        self.assertIn("His current company is FutureCo.", context)
        self.assertIn("FutureCo", context)
        self.assertNotIn("His current company is Chronostep.", context)

    def test_ai_context_job_question_uses_current_company(self):
        roadmaps = [
            {"company_name": "FutureCo", "period": "2025 - Present", "role_title": "Senior Engineer", "role_title_i18n": None, "sort_order": 2},
        ]
        service = ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext):
            context = service._ai_context()
        self.assertIn("Q: What is your job?", context)
        self.assertIn("I am currently working as a Senior Engineer at FutureCo.", context)
        self.assertNotIn("currently at Chronostep", context)

    def test_qa_item_job_question_uses_current_company(self):
        roadmaps = [
            {"company_name": "FutureCo", "period": "2025 - Present", "role_title": "Senior Engineer", "role_title_i18n": None, "sort_order": 2},
        ]
        service = ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext):
            qa = service.get_qa_data()
        job = next(item for item in qa if item["question"] == "What is your job?")
        self.assertIn("Senior Engineer at FutureCo", job["answer"])

    def test_ai_context_includes_company_details_from_roadmaps(self):
        roadmaps = [
            {
                "company_name": "Chronostep",
                "period": "2024 - Present",
                "role_title": "Software Engineer",
                "role_title_i18n": None,
                "location": "Cebu City",
                "definition": "Software development company.",
                "summary": "Builds web and mobile products.",
                "highlights": ["Full stack", "Internal tools"],
            },
        ]
        service = ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))
        context = service._ai_context()
        self.assertIn("COMPANY: Chronostep", context)
        self.assertIn("COMPANY LOCATION: Cebu City", context)
        self.assertIn("COMPANY DEFINITION: Software development company.", context)
        self.assertIn("COMPANY HIGHLIGHTS: Full stack; Internal tools", context)


class ChatServiceContentTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, **services):
        service = ChatService(
            key_project_service=services.get("projects"),
            company_roadmap_service=services.get("roadmaps"),
            gallery_service=services.get("gallery"),
            video_service=services.get("video"),
            music_service=services.get("music"),
        )
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value="en"), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message, QA)

    def _projects(self, count):
        return [
            {"title": {"en": f"Project {i + 1}"}, "description": {"en": f"Desc {i + 1}"}, "stack": "Flask", "status": "shipped"}
            for i in range(count)
        ]

    def test_projects_lists_titles(self):
        result = self._resolve("what projects have you built?", projects=_make_service("get_active_key_projects", self._projects(3)))
        self.assertIn("Key projects:", result["answer"])
        self.assertIn("Project 1", result["answer"])

    def test_projects_caps_at_six_with_count(self):
        result = self._resolve("projects", projects=_make_service("get_active_key_projects", self._projects(8)))
        self.assertIn("Project 6", result["answer"])
        self.assertNotIn("Project 7", result["answer"])
        self.assertIn("and 2 more", result["answer"])

    def test_projects_per_project_lookup(self):
        data = [
            {"title": {"en": "JAOM-CONNECT"}, "description": {"en": "Community platform."}, "stack": "Angular • Laravel", "status": "shipped"},
            {"title": {"en": "AI Voice Recognition"}, "description": {"en": "Voice app."}, "stack": "Python", "status": "in progress"},
        ]
        result = self._resolve("tell me about your jaom-connect project", projects=_make_service("get_active_key_projects", data))
        self.assertEqual(result["matched_question"], "JAOM-CONNECT")
        self.assertIn("Community platform", result["answer"])
        self.assertIn("Angular • Laravel", result["answer"])
        self.assertNotIn("AI Voice Recognition", result["answer"])

    def test_projects_empty(self):
        result = self._resolve("projects", projects=_make_service("get_active_key_projects", []))
        self.assertIn("No items found", result["answer"])

    def test_projects_unavailable_without_service(self):
        result = self._resolve("projects")
        self.assertIn("unavailable right now", result["answer"])

    def test_experience_formats_roles(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2021 - 2022", "role_title": "Intern", "role_title_i18n": {"en": "Software Engineer Intern"}},
            {"company_name": "Chronostep", "period": "2022 - Present", "role_title": "Developer", "role_title_i18n": None},
        ]
        result = self._resolve("your experience", roadmaps=_make_service("get_active_company_roadmaps", roadmaps))
        self.assertIn("Experience:", result["answer"])
        self.assertIn("Software Engineer Intern @ TrustArc (2021 - 2022)", result["answer"])
        self.assertIn("Developer @ Chronostep (2022 - Present)", result["answer"])

    def test_experience_unavailable_without_service(self):
        result = self._resolve("company roadmap")
        self.assertIn("unavailable right now", result["answer"])

    def test_contributions_at_company_routes_to_experience_not_donation(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2021 - 2022", "role_title": "Intern", "role_title_i18n": {"en": "Software Engineer Intern"}},
            {"company_name": "Chronostep", "period": "2024 - Present", "role_title": "Software Engineer", "role_title_i18n": None},
        ]
        result = self._resolve(
            "tell me your contributions in chronostep",
            roadmaps=_make_service("get_active_company_roadmaps", roadmaps),
        )
        self.assertIn("Chronostep", result["answer"])
        self.assertNotIn("Donation", result["answer"])
        self.assertNotIn("Python", result["answer"])

    def test_gallery_lists_titles_with_count(self):
        items = [{"title": {"en": f"Photo {i + 1}"}} for i in range(8)]
        result = self._resolve("gallery photos", gallery=_make_service("search_gallery_paginated", (items, 8)))
        self.assertIn("Gallery photos:", result["answer"])
        self.assertIn("Photo 6", result["answer"])
        self.assertNotIn("Photo 7", result["answer"])
        self.assertIn("and 2 more", result["answer"])

    def test_gallery_empty(self):
        result = self._resolve("gallery", gallery=_make_service("search_gallery_paginated", ([], 0)))
        self.assertIn("No items found", result["answer"])

    def test_gallery_count_from_db(self):
        result = self._resolve(
            "how many photos do you have",
            gallery=_make_service("search_gallery_paginated", ([{"title": {"en": "X"}}], 8)),
        )
        self.assertEqual(result["answer"], "I have 8 photos in my gallery.")

    def test_vlog_count_from_db(self):
        result = self._resolve(
            "how many vlogs do you have",
            video=_make_service("search_video_paginated", ([{"title": {"en": "V"}}], 3)),
        )
        self.assertEqual(result["answer"], "I have 3 vlogs in my collection.")

    def test_music_count_from_db(self):
        result = self._resolve(
            "how many songs do you have",
            music=_make_service("get_paginated_music_list", ([{"title": "A", "artist": "B"}], 5)),
        )
        self.assertEqual(result["answer"], "I have 5 songs in my collection.")

    def test_kb_guard_answers_music_categories(self):
        result = self._resolve("what music categories are there")
        self.assertIn("Rap", result["answer"])
        self.assertIn("Focus", result["answer"])

    def test_kb_guard_answers_download(self):
        result = self._resolve("can i download the songs")
        self.assertIn("downloaded", result["answer"])

    def test_kb_guard_answers_visualizer(self):
        result = self._resolve("does your music player have a visualizer")
        self.assertIn("8 beat visualizer modes", result["answer"])

    def test_kb_guard_answers_like_comment(self):
        result = self._resolve("can i like your photos")
        self.assertEqual(result["matched_question"], "How do I like a photo?")
        self.assertIn("like action", result["answer"])

    def test_kb_guard_answers_page_description(self):
        result = self._resolve("what is on the gallery page")
        self.assertEqual(result["matched_question"], "What is on the Gallery page?")
        self.assertIn("gallery channel", result["answer"])

    def test_vlog_lists_titles(self):
        items = [{"title": {"en": f"Vlog {i}"}} for i in range(3)]
        result = self._resolve("your vlog", video=_make_service("search_video_paginated", (items, 3)))
        self.assertIn("Recent vlogs:", result["answer"])
        self.assertIn("Vlog 2", result["answer"])

    def test_music_lists_songs(self):
        items = [
            {"title": "Song A", "artist": "Artist A"},
            {"title": "Song B", "artist": "Artist B"},
        ]
        result = self._resolve("music", music=_make_service("get_paginated_music_list", (items, 2)))
        self.assertIn("Songs:", result["answer"])
        self.assertIn("Song A - Artist A", result["answer"])


class ChatServiceSuggestTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, qa):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return self.service.resolve(message, qa)

    def test_partial_match_suggests_questions(self):
        qa = [
            {"question": "Where did you attend high school?", "answer": "A local high school in Negros Oriental."},
        ]
        result = self._resolve("where did you attend class", qa)
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("Did you mean one of these?", result["answer"])
        self.assertIn("Where did you attend high school?", result["answer"])

    def test_suggest_band_below_match_threshold(self):
        qa = [
            {"question": "Where did you attend high school?", "answer": "A local high school in Negros Oriental."},
        ]
        best = self.service._find_best_qa(self.service._expand_message("where did you attend class"), qa)
        self.assertIsNotNone(best)
        self.assertGreaterEqual(best["score"], 0.28)
        self.assertLess(best["score"], 0.36)


class ChatServiceMultiTurnTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _projects(self, count):
        return [
            {"title": {"en": f"Project {i + 1}"}, "description": {"en": f"Desc {i + 1}"}, "stack": "Flask", "status": "shipped"}
            for i in range(count)
        ]

    def _use_projects(self, count):
        self.service = ChatService(key_project_service=_make_service("get_active_key_projects", self._projects(count)))

    def _resolve(self, message, session_id="abc123", qa=None):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value="en"), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return self.service.resolve(message, qa if qa is not None else QA, session_id=session_id)

    def test_ordinal_follow_up_returns_item_detail(self):
        self._use_projects(3)
        self._resolve("projects")
        result = self._resolve("the second one")
        self.assertEqual(result["matched_question"], "Project 2")

    def test_ordinal_out_of_range(self):
        self._use_projects(2)
        self._resolve("projects")
        result = self._resolve("the fifth one")
        self.assertIn("I only have", result["answer"])
        self.assertIn("2", result["answer"])

    def test_tell_me_more_repeats_last_item(self):
        self._use_projects(3)
        self._resolve("tell me about your project 1")
        result = self._resolve("tell me more")
        self.assertEqual(result["matched_question"], "Project 1")

    def test_follow_up_needs_context(self):
        self._use_projects(3)
        result = self._resolve("the second one")
        self.assertIsNone(result["matched_question"])

    def test_girlfriend_pronoun_follow_up(self):
        self._resolve("tell me your gf")
        result = self._resolve("who is she")
        self.assertEqual(result["answer"], "Fiona Samantha Escarro.")

    def test_girlfriend_pronoun_follow_up_her(self):
        self._resolve("tell me about fiona")
        result = self._resolve("tell me more about her")
        self.assertEqual(result["answer"], "Fiona Samantha Escarro.")

    def test_girlfriend_pronoun_follow_up_contact_refused(self):
        self._resolve("tell me your gf")
        result = self._resolve("what is her contact number?")
        self.assertEqual(result["answer"], "I don't know about her contacts.")

    def test_girlfriend_pronoun_follow_up_needs_context(self):
        result = self._resolve("who is she")
        self.assertNotEqual(result["answer"], "Fiona Samantha Escarro.")

    def test_unrelated_math_beats_girlfriend_company(self):
        result = self._resolve("1 + 1?")
        self.assertIn("unrelated to my conversation", result["answer"])

    def test_girlfriend_pronoun_follow_up_company(self):
        self._resolve("tell me your gf")
        result = self._resolve("what company does she work at?")
        self.assertEqual(result["answer"], "She works at Teleperformance in IT Park.")

    def test_girlfriend_pronoun_follow_up_age(self):
        self._resolve("tell me your gf")
        result = self._resolve("what is her age?")
        self.assertEqual(result["answer"], f"Fiona is {_girlfriend_age()} years old. Her birthday is April 11, 2005.")

    def test_girlfriend_pronoun_follow_up_age_confirmation_yes(self):
        self._resolve("tell me your gf")
        age = _girlfriend_age()
        result = self._resolve(f"is she {age} years old today or not")
        self.assertEqual(result["answer"], f"Yes, she is {age} years old! Fiona was born on April 11, 2005.")

    def test_girlfriend_pronoun_follow_up_age_confirmation_no(self):
        self._resolve("tell me your gf")
        age = _girlfriend_age()
        result = self._resolve(f"is she {age + 1} years old")
        self.assertEqual(result["answer"], f"No, she is {age} years old, not {age + 1}. Fiona was born on April 11, 2005.")

    def test_girlfriend_age_follow_up_needs_context(self):
        result = self._resolve("what is her age?")
        self.assertNotIn("Fiona is", result["answer"])

    def test_girlfriend_age_follow_up_beats_ai(self):
        gemini = MagicMock()
        gemini.answer.return_value = "AI answer."
        self.service = ChatService(gemini_service=gemini)
        self._resolve("tell me your gf")
        gemini.answer.reset_mock()
        result = self._resolve("is she 21 years old today or not")
        self.assertIn("years old", result["answer"])
        self.assertIn("Fiona", result["answer"])
        gemini.answer.assert_not_called()

    def test_context_suggestions_on_fallback(self):
        self._use_projects(3)
        self._resolve("projects")
        result = self._resolve("tell me about the habitat of elephants")
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("Project 1", result["answer"])

    def test_how_about_new_topic_does_not_repeat_stale_list(self):
        gemini = MagicMock()
        gemini.answer.return_value = "Backend: Python, PHP, and SQL."
        self.service = ChatService(
            key_project_service=_make_service("get_active_key_projects", self._projects(3)),
            gemini_service=gemini,
        )
        self._resolve("projects")
        result = self._resolve("how about in backend")
        self.assertEqual(result["answer"], "Backend: Python, PHP, and SQL.")

    def test_how_about_this_one_still_lists_items(self):
        self._use_projects(3)
        self._resolve("projects")
        result = self._resolve("how about this one")
        self.assertEqual(result["action"], "expand_options")
        self.assertIn("Project 1", result["answer"])

    def test_has_item_reference(self):
        self.assertTrue(self.service._has_item_reference("how about this one"))
        self.assertTrue(self.service._has_item_reference("what about them"))
        self.assertTrue(self.service._has_item_reference("the second one"))
        self.assertFalse(self.service._has_item_reference("how about in backend"))
        self.assertFalse(self.service._has_item_reference("what about the weather"))


class ChatServiceContentMatchTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, **services):
        service = ChatService(
            key_project_service=services.get("projects"),
            company_roadmap_service=services.get("roadmaps"),
            gallery_service=services.get("gallery"),
            video_service=services.get("video"),
            music_service=services.get("music"),
        )
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value="en"), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message, QA)

    def test_project_description_lookup(self):
        data = [
            {"title": {"en": "JAOM-CONNECT"}, "description": {"en": "A community platform for local barangays."}, "stack": "Angular", "status": "shipped"},
            {"title": {"en": "Voice App"}, "description": {"en": "AI voice recognition app."}, "stack": "Python", "status": "in progress"},
        ]
        result = self._resolve("tell me about the community platform", projects=_make_service("get_active_key_projects", data))
        self.assertEqual(result["matched_question"], "JAOM-CONNECT")

    def test_experience_company_lookup(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2021 - 2022", "role_title": "Intern", "role_title_i18n": {"en": "Software Engineer Intern"}},
        ]
        result = self._resolve("tell me about trustarc", roadmaps=_make_service("get_active_company_roadmaps", roadmaps))
        self.assertEqual(result["matched_question"], "TrustArc")
        self.assertIn("Software Engineer Intern @ TrustArc", result["answer"])

    def test_music_artist_lookup(self):
        items = [
            {"title": "Song A", "artist": "Artist A"},
            {"title": "Song B", "artist": "Artist B"},
        ]
        result = self._resolve("tell me about artist b", music=_make_service("get_paginated_music_list", (items, 2)))
        self.assertEqual(result["matched_question"], "Song B")

    def test_generic_list_does_not_pick_item(self):
        items = [{"title": {"en": f"Photo {i}"}, "description": {"en": ""}, "tags": []} for i in range(3)]
        result = self._resolve("gallery photos", gallery=_make_service("search_gallery_paginated", (items, 3)))
        self.assertEqual(result["action"], None)
        self.assertIn("Gallery photos:", result["answer"])

    def test_gallery_description_lookup(self):
        items = [
            {"title": {"en": "Sunset"}, "description": {"en": "Golden sunset over the hills"}, "tags": []},
            {"title": {"en": "Beach Day"}, "description": {"en": "Sand and sea"}, "tags": []},
        ]
        result = self._resolve("show me the sunset hills photo", gallery=_make_service("search_gallery_paginated", (items, 2)))
        self.assertEqual(result["matched_question"], "Sunset")

    def test_hyphen_title_matches_space_query(self):
        long_desc = (
            "A comprehensive community platform that connects local barangays, residents, and municipal "
            "services through digital tools, enabling transparent governance and real-time updates."
        )
        data = [
            {"title": {"en": "JAOM-CONNECT"}, "description": {"en": long_desc}, "stack": "Angular", "status": "shipped"},
            {"title": {"en": "AI Voice Recognition"}, "description": {"en": "Voice app."}, "stack": "Python", "status": "in progress"},
        ]
        result = self._resolve("tell me about this jaom connect project", projects=_make_service("get_active_key_projects", data))
        self.assertEqual(result["matched_question"], "JAOM-CONNECT")
        self.assertIn("community platform", result["answer"])

    def test_long_description_does_not_dilute_title_match(self):
        long_desc = (
            "A comprehensive community platform that connects local barangays, residents, and municipal "
            "services through digital tools, enabling transparent governance and real-time updates across "
            "the whole municipality with mobile and web interfaces."
        )
        data = [
            {"title": {"en": "JAOM-CONNECT"}, "description": {"en": long_desc}, "stack": "Angular", "status": "shipped"},
        ]
        result = self._resolve("tell me about the jaom connect", projects=_make_service("get_active_key_projects", data))
        self.assertEqual(result["matched_question"], "JAOM-CONNECT")
        self.assertNotIn("Key projects:", result["answer"])

    def test_hyphen_title_vlog_lookup(self):
        items = [
            {"title": {"en": "Beach-Vibes Vlog"}, "description": {"en": ""}, "tags": []},
            {"title": {"en": "City Tour"}, "description": {"en": ""}, "tags": []},
        ]
        result = self._resolve("tell me about beach vibes", video=_make_service("search_video_paginated", (items, 2)))
        self.assertEqual(result["matched_question"], "Beach-Vibes Vlog")

    def test_hyphen_title_gallery_lookup(self):
        items = [
            {"title": {"en": "Sunset"}, "description": {"en": ""}, "tags": []},
            {"title": {"en": "Mountain-View"}, "description": {"en": ""}, "tags": []},
        ]
        result = self._resolve("show mountain view photo", gallery=_make_service("search_gallery_paginated", (items, 2)))
        self.assertEqual(result["matched_question"], "Mountain-View")


class ChatServiceFuzzyTopicTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, **services):
        service = ChatService(
            key_project_service=services.get("projects"),
            company_roadmap_service=services.get("roadmaps"),
        )
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value="en"), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message, QA)

    def test_typo_in_topic_word(self):
        result = self._resolve("projcts", projects=_make_service("get_active_key_projects", []))
        self.assertIn("No items found", result["answer"])

    def test_fuzzy_experience_word(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2021 - 2022", "role_title": "Intern", "role_title_i18n": {"en": "Software Engineer Intern"}},
        ]
        result = self._resolve("your experince", roadmaps=_make_service("get_active_company_roadmaps", roadmaps))
        self.assertIn("TrustArc", result["answer"])


class ChatServiceLocalizedAliasTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, locale="ceb"):
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value=locale), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return self.service.resolve(message, QA)

    def test_ceb_alias_lives(self):
        result = self._resolve("asa ka nagpuyo", "ceb")
        self.assertIn("Cabulihan", result["answer"])

    def test_fil_alias_name(self):
        result = self._resolve("ano pangalan mo", "fil_PH")
        self.assertIn("Joshua", result["answer"])


KB_TEXT = """\
# Test knowledge base

## What is your hobby?
I like drawing and coding.
Aliases: what do you do for fun, hobbies, your hobby

## Favorite Food
Key: food
I love adobo.

## Tell me about yourself
Key: about
I am a passionate software developer.
Aliases: about you, about yourself
"""


KB_TEXT_FUZZY = """\
# Fuzzy test kb

## Contact information
Key: contact
You can reach me on LinkedIn at joshua-linkedin.
Aliases: linkedin url, contact info, how to contact me
"""


KB_TEXT_L10N = """\
# Localized test kb

## What is your name?
My name is Joshua.
Aliases: who are you
Heading-ceb: Unsa imong pangalan?
Body-ceb: Si Joshua ko.
Aliases-ceb: kinsa ka, unsa imong pangalan
Heading-fil_PH: Ano pangalan mo?
Body-fil_PH: Si Joshua ako.
Aliases-fil_PH: sino ka, ano pangalan mo

## Hobby
Key: hobby
I like coding.
Heading-ceb: Unsa imong hobby?
Body-ceb: Ganahan ko mag-coding.
Aliases-ceb: unsa imong hobby
"""


class KnowledgeBaseServiceTests(unittest.TestCase):
    def test_parses_sections_headings_aliases_and_keys(self):
        kb = KnowledgeBaseService(text=KB_TEXT)
        sections = kb.sections()
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0]["heading"], "What is your hobby?")
        self.assertEqual(sections[0]["body"], "I like drawing and coding.")
        self.assertEqual(sections[0]["aliases"], ["what do you do for fun", "hobbies", "your hobby"])
        self.assertIsNone(sections[0]["key"])
        self.assertEqual(sections[1]["key"], "food")
        self.assertEqual(sections[1]["body"], "I love adobo.")
        self.assertEqual(sections[2]["key"], "about")
        self.assertEqual(sections[2]["aliases"], ["about you", "about yourself"])

    def test_missing_file_returns_empty(self):
        kb = KnowledgeBaseService(path="does/not/exist.md")
        self.assertEqual(kb.sections(), [])

    def test_results_are_cached(self):
        kb = KnowledgeBaseService(text=KB_TEXT)
        self.assertIs(kb.sections(), kb.sections())

    def test_parses_localized_fields(self):
        kb = KnowledgeBaseService(text=KB_TEXT_L10N)
        sections = kb.sections()
        self.assertEqual(len(sections), 2)
        first = sections[0]
        self.assertEqual(first["heading"], "What is your name?")
        self.assertEqual(first["body"], "My name is Joshua.")
        self.assertEqual(first["aliases"], ["who are you"])
        self.assertEqual(
            first["localized"]["ceb"],
            {
                "heading": "Unsa imong pangalan?",
                "body": "Si Joshua ko.",
                "aliases": ["kinsa ka", "unsa imong pangalan"],
            },
        )
        self.assertEqual(first["localized"]["fil_PH"]["heading"], "Ano pangalan mo?")
        self.assertEqual(first["localized"]["fil_PH"]["body"], "Si Joshua ako.")
        self.assertEqual(
            first["localized"]["fil_PH"]["aliases"],
            ["sino ka", "ano pangalan mo"],
        )
        self.assertEqual(sections[1]["localized"]["ceb"]["body"], "Ganahan ko mag-coding.")


class ChatServiceKnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.kb = KnowledgeBaseService(text=KB_TEXT)
        self.service = ChatService(knowledge_base_service=self.kb)

    def _resolve(self, message, service=None):
        service = service or self.service
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value="en"), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message)

    def test_get_qa_data_derives_from_guide(self):
        qa = self.service.get_qa_data()
        self.assertEqual(len(qa), 3)
        self.assertEqual(qa[0]["question"], "What is your hobby?")
        self.assertEqual(qa[0]["answer"], "I like drawing and coding.")
        self.assertEqual(qa[0]["aliases"], ["what do you do for fun", "hobbies", "your hobby"])

    def test_new_fact_answered_from_guide_heading(self):
        result = self._resolve("what is your hobby?")
        self.assertEqual(result["matched_question"], "What is your hobby?")
        self.assertIn("drawing and coding", result["answer"])

    def test_new_fact_answered_from_guide_alias(self):
        result = self._resolve("what do you do for fun?")
        self.assertIn("drawing and coding", result["answer"])

    def test_guide_key_section_answered(self):
        result = self._resolve("I want to know your favorite food")
        self.assertIn("adobo", result["answer"])

    def test_static_topic_reads_from_guide_key(self):
        result = self._resolve("tell me about yourself")
        self.assertIn("passionate software developer", result["answer"])

    def test_real_guide_file_loads_and_answers(self):
        result = self._resolve("what genre do you like?", service=ChatService())
        self.assertIn("rap", result["answer"])

    def test_kb_answers_career_journey_not_ai(self):
        result = self._resolve("how did you start", service=ChatService())
        self.assertEqual(result["matched_question"], "What is your career journey?")
        self.assertIn("TrustArc", result["answer"])

    def test_advice_not_intercepted_by_developers_intent(self):
        result = self._resolve("what advice do you have for aspiring developers", service=ChatService())
        self.assertEqual(result["matched_question"], "What advice do you have for aspiring developers?")
        self.assertIn("internships", result["answer"])

    def test_share_question_answered_by_like_comment_section(self):
        result = self._resolve("how do i share a photo", service=ChatService())
        self.assertEqual(result["matched_question"], "Can I like or comment on photos and videos?")
        self.assertIn("sharing", result["answer"])

    def test_typo_alias_answered_via_fuzzy_matching(self):
        kb = KnowledgeBaseService(text=KB_TEXT_FUZZY)
        service = ChatService(knowledge_base_service=kb)
        result = self._resolve("can you tell me uour linkendin url", service=service)
        self.assertIn("linkedin", result["answer"])
        self.assertEqual(result["matched_question"], "Contact information")


class ChatServiceKnowledgeBaseLocalizedTests(unittest.TestCase):
    def setUp(self):
        self.kb = KnowledgeBaseService(text=KB_TEXT_L10N)
        self.service = ChatService(knowledge_base_service=self.kb)

    def _resolve(self, message, locale="ceb", service=None):
        service = service or self.service
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.get_locale", return_value=locale), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message)

    def test_get_qa_data_localizes_cebuano(self):
        service = ChatService(knowledge_base_service=self.kb)
        with patch("app.Services.ChatService.get_locale", return_value="ceb"):
            qa = service.get_qa_data()
        self.assertEqual(qa[0]["question"], "Unsa imong pangalan?")
        self.assertEqual(qa[0]["answer"], "Si Joshua ko.")
        self.assertEqual(
            qa[0]["aliases"],
            ["who are you", "kinsa ka", "unsa imong pangalan"],
        )

    def test_get_qa_data_localizes_tagalog(self):
        service = ChatService(knowledge_base_service=self.kb)
        with patch("app.Services.ChatService.get_locale", return_value="fil_PH"):
            qa = service.get_qa_data()
        self.assertEqual(qa[0]["question"], "Ano pangalan mo?")
        self.assertEqual(qa[0]["answer"], "Si Joshua ako.")

    def test_get_qa_data_english_stays_english(self):
        service = ChatService(knowledge_base_service=self.kb)
        with patch("app.Services.ChatService.get_locale", return_value="en"):
            qa = service.get_qa_data()
        self.assertEqual(qa[0]["question"], "What is your name?")
        self.assertEqual(qa[0]["answer"], "My name is Joshua.")
        self.assertEqual(qa[0]["aliases"], ["who are you"])

    def test_resolve_answers_in_cebuano(self):
        result = self._resolve("kinsa ka", "ceb")
        self.assertEqual(result["answer"], "Si Joshua ko.")

    def test_resolve_answers_in_tagalog(self):
        result = self._resolve("ano pangalan mo", "fil_PH")
        self.assertEqual(result["answer"], "Si Joshua ako.")

    def test_key_section_reply_localized(self):
        result = self._resolve("unsa imong hobby", "ceb")
        self.assertEqual(result["answer"], "Ganahan ko mag-coding.")

    def test_untranslated_section_falls_back_to_english(self):
        kb = KnowledgeBaseService(text=KB_TEXT)
        service = ChatService(knowledge_base_service=kb)
        result = self._resolve("what is your hobby?", "ceb", service=service)
        self.assertEqual(result["answer"], "I like drawing and coding.")


class ChatServiceLocalizedCountTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService()

    def _resolve(self, message, locale, replies, **services):
        service = ChatService(
            gallery_service=services.get("gallery"),
            video_service=services.get("video"),
            music_service=services.get("music"),
        )
        with patch("app.Services.ChatService.gettext", side_effect=_localized_gettext_factory(replies)), \
             patch("app.Services.ChatService.get_locale", return_value=locale), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message, QA)

    def test_ceb_gallery_count(self):
        result = self._resolve(
            "pila ka photos ang naa nimo",
            "ceb",
            {"chat_gallery_count_reply": "Naa koy {total} nga mga litrato sa akong gallery."},
            gallery=_make_service("search_gallery_paginated", ([{"title": {"en": "X"}}], 8)),
        )
        self.assertEqual(result["answer"], "Naa koy 8 nga mga litrato sa akong gallery.")

    def test_ceb_vlog_count(self):
        result = self._resolve(
            "tagpila ka vlogs",
            "ceb",
            {"chat_vlog_count_reply": "Naa koy {total} nga mga vlog sa akong koleksyon."},
            video=_make_service("search_video_paginated", ([{"title": {"en": "V"}}], 3)),
        )
        self.assertEqual(result["answer"], "Naa koy 3 nga mga vlog sa akong koleksyon.")

    def test_fil_music_count(self):
        result = self._resolve(
            "ilan ba ang songs mo",
            "fil_PH",
            {"chat_music_count_reply": "Mayroon akong {total} na mga kanta sa aking koleksyon."},
            music=_make_service("get_paginated_music_list", ([{"title": "A", "artist": "B"}], 5)),
        )
        self.assertEqual(result["answer"], "Mayroon akong 5 na mga kanta sa aking koleksyon.")


class ChatServiceDynamicJobTests(unittest.TestCase):
    def _service(self, roadmaps=None):
        return ChatService(company_roadmap_service=_make_service("get_active_company_roadmaps", roadmaps))

    def _resolve(self, service, message, locale="en", replies=None):
        with patch("app.Services.ChatService.gettext", side_effect=_localized_gettext_factory(replies or {})), \
             patch("app.Services.ChatService.get_locale", return_value=locale), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return service.resolve(message)

    def test_job_answer_is_dynamic_from_roadmaps(self):
        roadmaps = [
            {"company_name": "TrustArc", "period": "2023", "role_title": "Intern", "role_title_i18n": None, "sort_order": 2},
            {"company_name": "Chronostep", "period": "2024 - Present", "role_title": "Software Engineer", "role_title_i18n": None, "sort_order": 4},
        ]
        result = self._resolve(self._service(roadmaps), "what is your current company")
        self.assertEqual(result["answer"], "I am currently working as a Software Engineer at Chronostep.")
        self.assertEqual(result["matched_question"], "What is your job?")

    def test_job_picks_highest_sort_when_no_present(self):
        roadmaps = [
            {"company_name": "OldCo", "period": "2020 - 2021", "role_title": "Tech Lead", "role_title_i18n": None, "sort_order": 1},
        ]
        result = self._resolve(self._service(roadmaps), "What is your job?")
        self.assertEqual(result["answer"], "I am currently working as a Tech Lead at OldCo.")

    def test_job_localized_dynamic_reply(self):
        roadmaps = [
            {"company_name": "Chronostep", "period": "2024 - Present", "role_title": "Software Engineer", "role_title_i18n": None, "sort_order": 4},
        ]
        replies = {"chat_current_role_reply": "Kasamtangan nagtrabaho ko isip {role} sa {company}."}
        result = self._resolve(self._service(roadmaps), "unsa imong kasamtangan nga kompanya", "ceb", replies)
        self.assertEqual(result["answer"], "Kasamtangan nagtrabaho ko isip Software Engineer sa Chronostep.")

    def test_job_uses_localized_role_when_available(self):
        roadmaps = [
            {"company_name": "Chronostep", "period": "2024 - Present", "role_title": "Software Engineer",
             "role_title_i18n": {"en": "Software Engineer", "ceb": "Inhenyero sa Software"}, "sort_order": 4},
        ]
        replies = {"chat_current_role_reply": "Kasamtangan nagtrabaho ko isip {role} sa {company}."}
        result = self._resolve(self._service(roadmaps), "what is your current company", "ceb", replies)
        self.assertEqual(result["answer"], "Kasamtangan nagtrabaho ko isip Inhenyero sa Software sa Chronostep.")

    def test_job_falls_back_to_static_without_service(self):
        result = self._resolve(ChatService(), "What is your job?")
        self.assertIn("Software Engineer currently at Chronostep", result["answer"])

    def test_job_falls_back_to_static_on_empty_roadmaps(self):
        result = self._resolve(self._service([]), "what is your current company")
        self.assertIn("Software Engineer currently at Chronostep", result["answer"])


class RealGuideLocalizationTests(unittest.TestCase):
    def test_real_guide_is_localized_throughout(self):
        kb = KnowledgeBaseService()
        sections = kb.sections()
        self.assertEqual(len(sections), 172)
        headings = [section["heading"] for section in sections]
        self.assertEqual(len(headings), len(set(headings)))
        self.assertTrue(all(section["body"] for section in sections))
        for section in sections:
            for locale in ("ceb", "fil_PH"):
                loc = (section.get("localized") or {}).get(locale) or {}
                self.assertTrue(loc.get("heading"), f"missing {locale} heading for {section['heading']}")
                self.assertTrue(loc.get("body"), f"missing {locale} body for {section['heading']}")
                self.assertTrue(loc.get("aliases"), f"missing {locale} aliases for {section['heading']}")

    def test_real_guide_localized_qna_resolves(self):
        service = ChatService()
        cases = [
            ("asa ka nagpuyo", "ceb", "Cabulihan"),
            ("ano pangalan mo", "fil_PH", "Joshua"),
            ("unsa imong pangalan", "ceb", "Joshua"),
            ("saan ka nakatira", "fil_PH", "Cabulihan"),
        ]
        for message, locale, needle in cases:
            with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
                 patch("app.Services.ChatService.get_locale", return_value=locale), \
                 patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
                result = service.resolve(message)
            self.assertIn(needle, result["answer"], f"{message} in {locale}")


if __name__ == "__main__":
    unittest.main()
