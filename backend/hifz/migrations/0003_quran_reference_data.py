"""Reference data for Quran programs: Noorani Qaida lessons and standard checklists.

Idempotent (get_or_create) and editable afterwards from the portal.
"""
from django.db import migrations

QAIDA = [
    (1, "Huroof Mufradat (single letters)", "الحروف المفردات"),
    (2, "Huroof Murakkabat (joined letters)", "الحروف المركبات"),
    (3, "Huroof Muqatta'at (disjointed letters)", "الحروف المقطعات"),
    (4, "Harakaat — Fathah, Kasrah, Dammah", "الحركات"),
    (5, "Tanween", "التنوين"),
    (6, "Exercise on Harakaat & Tanween", "تمرين"),
    (7, "Khari Harakaat (standing vowels)", "الحركات القائمة"),
    (8, "Huroof Maddah (Alif, Waw, Ya)", "حروف المد"),
    (9, "Huroof Leen", "حروف اللين"),
    (10, "Exercise on Maddah & Leen", "تمرين"),
    (11, "Sukoon / Jazm", "السكون"),
    (12, "Exercise on Sukoon", "تمرين"),
    (13, "Tashdeed", "التشديد"),
    (14, "Tashdeed with Tashdeed", "التشديد مع التشديد"),
    (15, "Tashdeed after Huroof Maddah", "التشديد بعد حروف المد"),
    (16, "Rules of Waqf (stopping)", "قواعد الوقف"),
    (17, "Revision & reading practice from the Qur'an", "المراجعة"),
]

C = "category"
ITEMS = [
    # Kalimas
    {C: "kalima", "title": "First Kalimah — Tayyib", "arabic": "لَا إِلٰهَ إِلَّا اللّٰهُ مُحَمَّدٌ رَّسُوْلُ اللّٰهِ",
     "translation": "There is no god but Allah; Muhammad is the Messenger of Allah."},
    {C: "kalima", "title": "Second Kalimah — Shahadah", "arabic": "أَشْهَدُ أَنْ لَّا إِلٰهَ إِلَّا اللّٰهُ وَحْدَهُ لَا شَرِيْكَ لَهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُوْلُهُ",
     "translation": "I bear witness that there is no god but Allah, alone without partner, and I bear witness that Muhammad is His servant and Messenger."},
    {C: "kalima", "title": "Third Kalimah — Tamjeed", "arabic": "سُبْحَانَ اللّٰهِ وَالْحَمْدُ لِلّٰهِ وَلَا إِلٰهَ إِلَّا اللّٰهُ وَاللّٰهُ أَكْبَرُ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللّٰهِ الْعَلِيِّ الْعَظِيْمِ",
     "translation": "Glory be to Allah, all praise is for Allah, there is no god but Allah, Allah is the Greatest; there is no might nor power except with Allah, the Most High, the Most Great."},
    {C: "kalima", "title": "Fourth Kalimah — Tawheed", "arabic": "لَا إِلٰهَ إِلَّا اللّٰهُ وَحْدَهُ لَا شَرِيْكَ لَهُ لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ يُحْيِيْ وَيُمِيْتُ وَهُوَ حَيٌّ لَّا يَمُوْتُ أَبَدًا أَبَدًا ذُو الْجَلَالِ وَالْإِكْرَامِ بِيَدِهِ الْخَيْرُ وَهُوَ عَلٰى كُلِّ شَيْءٍ قَدِيْرٌ",
     "translation": "There is no god but Allah, alone without partner; His is the dominion and His the praise. He gives life and causes death, and He is Ever-Living and never dies. Possessor of majesty and honour; in His hand is all good, and He has power over all things."},
    {C: "kalima", "title": "Fifth Kalimah — Istighfar", "arabic": "أَسْتَغْفِرُ اللّٰهَ رَبِّيْ مِنْ كُلِّ ذَنْبٍ أَذْنَبْتُهُ عَمَدًا أَوْ خَطَأً سِرًّا أَوْ عَلَانِيَةً وَأَتُوْبُ إِلَيْهِ مِنَ الذَّنْبِ الَّذِيْ أَعْلَمُ وَمِنَ الذَّنْبِ الَّذِيْ لَا أَعْلَمُ إِنَّكَ أَنْتَ عَلَّامُ الْغُيُوْبِ وَسَتَّارُ الْعُيُوْبِ وَغَفَّارُ الذُّنُوْبِ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللّٰهِ الْعَلِيِّ الْعَظِيْمِ",
     "translation": "I seek forgiveness from Allah, my Lord, for every sin I committed knowingly or unknowingly, secretly or openly, and I turn to Him in repentance."},
    {C: "kalima", "title": "Sixth Kalimah — Radd-e-Kufr", "arabic": "اَللّٰهُمَّ إِنِّيْ أَعُوْذُ بِكَ مِنْ أَنْ أُشْرِكَ بِكَ شَيْئًا وَّأَنَا أَعْلَمُ بِهِ وَأَسْتَغْفِرُكَ لِمَا لَا أَعْلَمُ بِهِ تُبْتُ عَنْهُ وَتَبَرَّأْتُ مِنَ الْكُفْرِ وَالشِّرْكِ وَالْكِذْبِ وَالْغِيْبَةِ وَالْبِدْعَةِ وَالنَّمِيْمَةِ وَالْفَوَاحِشِ وَالْبُهْتَانِ وَالْمَعَاصِيْ كُلِّهَا وَأَسْلَمْتُ وَأَقُوْلُ لَا إِلٰهَ إِلَّا اللّٰهُ مُحَمَّدٌ رَّسُوْلُ اللّٰهِ",
     "translation": "O Allah, I seek refuge in You from knowingly associating anything with You, and I seek Your forgiveness for what I do not know. I repent from it and free myself from disbelief, polytheism, lying, backbiting, innovation, tale-bearing, indecency, slander and all sins. I submit and declare: there is no god but Allah, Muhammad is the Messenger of Allah."},
    {C: "aqaid", "title": "Iman-e-Mujmal", "arabic": "آمَنْتُ بِاللّٰهِ كَمَا هُوَ بِأَسْمَائِهِ وَصِفَاتِهِ وَقَبِلْتُ جَمِيْعَ أَحْكَامِهِ",
     "translation": "I believe in Allah as He is with His names and attributes, and I accept all His commands."},
    {C: "aqaid", "title": "Iman-e-Mufassal", "arabic": "آمَنْتُ بِاللّٰهِ وَمَلَائِكَتِهِ وَكُتُبِهِ وَرُسُلِهِ وَالْيَوْمِ الْآخِرِ وَالْقَدْرِ خَيْرِهِ وَشَرِّهِ مِنَ اللّٰهِ تَعَالٰى وَالْبَعْثِ بَعْدَ الْمَوْتِ",
     "translation": "I believe in Allah, His angels, His books, His messengers, the Last Day, that destiny — good and bad — is from Allah, and in resurrection after death."},
    {C: "aqaid", "title": "Five pillars of Islam (explain)", "arabic": "", "translation": "Shahadah, Salah, Zakah, Sawm, Hajj."},
    # Masnoon duas
    {C: "dua", "title": "Before eating", "arabic": "بِسْمِ اللّٰهِ", "translation": "In the name of Allah. (If forgotten at the start: بِسْمِ اللّٰهِ أَوَّلَهُ وَآخِرَهُ)", "reference": "Sahih al-Bukhari 5376; Abu Dawud 3767"},
    {C: "dua", "title": "After eating", "arabic": "اَلْحَمْدُ لِلّٰهِ الَّذِيْ أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مُسْلِمِيْنَ", "translation": "All praise is for Allah who fed us, gave us drink and made us Muslims.", "reference": "Abu Dawud 3850; Tirmidhi 3457"},
    {C: "dua", "title": "Before sleeping", "arabic": "بِاسْمِكَ اللّٰهُمَّ أَمُوْتُ وَأَحْيَا", "translation": "In Your name, O Allah, I die and I live.", "reference": "Sahih al-Bukhari 6324"},
    {C: "dua", "title": "On waking up", "arabic": "اَلْحَمْدُ لِلّٰهِ الَّذِيْ أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُوْرُ", "translation": "All praise is for Allah who gave us life after causing us to die, and to Him is the resurrection.", "reference": "Sahih al-Bukhari 6324"},
    {C: "dua", "title": "Entering the toilet", "arabic": "اَللّٰهُمَّ إِنِّيْ أَعُوْذُ بِكَ مِنَ الْخُبُثِ وَالْخَبَائِثِ", "translation": "O Allah, I seek refuge in You from the male and female devils.", "reference": "Sahih al-Bukhari 142"},
    {C: "dua", "title": "Leaving the toilet", "arabic": "غُفْرَانَكَ", "translation": "I seek Your forgiveness.", "reference": "Abu Dawud 30; Tirmidhi 7"},
    {C: "dua", "title": "Leaving home", "arabic": "بِسْمِ اللّٰهِ تَوَكَّلْتُ عَلَى اللّٰهِ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللّٰهِ", "translation": "In the name of Allah, I rely on Allah; there is no might nor power except with Allah.", "reference": "Abu Dawud 5095; Tirmidhi 3426"},
    {C: "dua", "title": "Entering the masjid", "arabic": "اَللّٰهُمَّ افْتَحْ لِيْ أَبْوَابَ رَحْمَتِكَ", "translation": "O Allah, open for me the doors of Your mercy.", "reference": "Sahih Muslim 713"},
    {C: "dua", "title": "Leaving the masjid", "arabic": "اَللّٰهُمَّ إِنِّيْ أَسْأَلُكَ مِنْ فَضْلِكَ", "translation": "O Allah, I ask You of Your bounty.", "reference": "Sahih Muslim 713"},
    {C: "dua", "title": "After wudu", "arabic": "أَشْهَدُ أَنْ لَّا إِلٰهَ إِلَّا اللّٰهُ وَحْدَهُ لَا شَرِيْكَ لَهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُوْلُهُ", "translation": "I bear witness that there is no god but Allah, alone without partner, and that Muhammad is His servant and Messenger.", "reference": "Sahih Muslim 234"},
    {C: "dua", "title": "For increase in knowledge", "arabic": "رَّبِّ زِدْنِيْ عِلْمًا", "translation": "My Lord, increase me in knowledge.", "reference": "Surah Ta-Ha 20:114"},
    {C: "dua", "title": "For parents", "arabic": "رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِيْ صَغِيْرًا", "translation": "My Lord, have mercy on them as they raised me when I was small.", "reference": "Surah Al-Isra 17:24"},
    {C: "dua", "title": "Good in this world and the next", "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ", "translation": "Our Lord, give us good in this world and good in the Hereafter, and protect us from the punishment of the Fire.", "reference": "Surah Al-Baqarah 2:201"},
    {C: "dua", "title": "On sneezing (and the reply)", "arabic": "اَلْحَمْدُ لِلّٰهِ — يَرْحَمُكَ اللّٰهُ", "translation": "All praise is for Allah — (reply) May Allah have mercy on you.", "reference": "Sahih al-Bukhari 6224"},
    # Ahadith
    {C: "hadith", "title": "Actions are by intentions", "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ", "translation": "Actions are only by intentions.", "reference": "Sahih al-Bukhari 1"},
    {C: "hadith", "title": "The best of you learn and teach the Qur'an", "arabic": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ", "translation": "The best of you are those who learn the Qur'an and teach it.", "reference": "Sahih al-Bukhari 5027"},
    {C: "hadith", "title": "Religion is sincere advice", "arabic": "الدِّيْنُ النَّصِيْحَةُ", "translation": "The religion is sincere advice (naseehah).", "reference": "Sahih Muslim 55"},
    {C: "hadith", "title": "Purity is half of faith", "arabic": "الطُّهُوْرُ شَطْرُ الْإِيْمَانِ", "translation": "Purification is half of faith.", "reference": "Sahih Muslim 223"},
    {C: "hadith", "title": "Speak good or remain silent", "arabic": "مَنْ كَانَ يُؤْمِنُ بِاللّٰهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ", "translation": "Whoever believes in Allah and the Last Day, let him speak good or remain silent.", "reference": "Sahih al-Bukhari 6018; Sahih Muslim 47"},
    {C: "hadith", "title": "Love for your brother", "arabic": "لَا يُؤْمِنُ أَحَدُكُمْ حَتّٰى يُحِبَّ لِأَخِيْهِ مَا يُحِبُّ لِنَفْسِهِ", "translation": "None of you truly believes until he loves for his brother what he loves for himself.", "reference": "Sahih al-Bukhari 13"},
    {C: "hadith", "title": "The Muslim is safe from tongue and hand", "arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُوْنَ مِنْ لِسَانِهِ وَيَدِهِ", "translation": "A Muslim is one from whose tongue and hand the Muslims are safe.", "reference": "Sahih al-Bukhari 10"},
    {C: "hadith", "title": "Modesty is part of faith", "arabic": "الْحَيَاءُ مِنَ الْإِيْمَانِ", "translation": "Modesty is part of faith.", "reference": "Sahih al-Bukhari 24"},
    {C: "hadith", "title": "Do not become angry", "arabic": "لَا تَغْضَبْ", "translation": "Do not become angry.", "reference": "Sahih al-Bukhari 6116"},
    {C: "hadith", "title": "Smiling is charity", "arabic": "تَبَسُّمُكَ فِيْ وَجْهِ أَخِيْكَ لَكَ صَدَقَةٌ", "translation": "Your smiling in the face of your brother is charity.", "reference": "Jami' at-Tirmidhi 1956"},
]
TAJWEED = ["Makharij al-Huroof (articulation points)", "Sifaat al-Huroof (letter characteristics)", "Isti'adhah & Basmalah",
           "Noon Sakinah & Tanween — Izhar", "Noon Sakinah & Tanween — Idgham (with / without Ghunnah)",
           "Noon Sakinah & Tanween — Iqlab", "Noon Sakinah & Tanween — Ikhfa", "Meem Sakinah — Ikhfa Shafawi",
           "Meem Sakinah — Idgham Shafawi", "Meem Sakinah — Izhar Shafawi", "Ghunnah (Noon & Meem Mushaddad)",
           "Qalqalah", "Tafkheem & Tarqeeq (heavy & light letters, Ra, Lam of Allah)", "Lam Shamsiyyah & Qamariyyah",
           "Madd Tabee'i (natural)", "Madd Muttasil", "Madd Munfasil", "Madd Lazim", "Madd 'Arid lis-Sukoon",
           "Waqf & Ibtida (stopping and starting)"]
QIRAAT = ["Riwayah of Hafs 'an 'Asim", "Riwayah of Shu'bah 'an 'Asim", "Riwayah of Warsh 'an Nafi'", "Riwayah of Qalun 'an Nafi'",
          "Qira'at Sab'ah (the seven readings)"]
SURAHS = ["Al-Fatihah", "Ayat al-Kursi (Al-Baqarah 2:255)", "An-Nas", "Al-Falaq", "Al-Ikhlas", "Al-Masad", "An-Nasr", "Al-Kafirun",
          "Al-Kawthar", "Al-Ma'un", "Quraysh", "Al-Fil", "Al-Asr", "Al-Mulk", "Ya-Sin"]
NAMAZ = ["Wudu — practical", "Ghusl — method (oral)", "Tayammum — practical", "Adhan", "Iqamah", "Sana", "Ta'awwudh & Tasmiyah",
         "Tasbeeh of Ruku & Sujood", "Tashahhud (At-Tahiyyat)", "Durood-e-Ibrahim", "Dua after Durood", "Dua-e-Qunoot (Witr)",
         "Complete two-rak'ah Salah demonstration", "Janazah Salah — method (oral)"]


def forwards(apps, schema_editor):
    QaidaLesson = apps.get_model("hifz", "QaidaLesson")
    ChecklistItem = apps.get_model("hifz", "ChecklistItem")
    for n, title, ar in QAIDA:
        QaidaLesson.objects.get_or_create(number=n, defaults={"title": title, "title_arabic": ar})
    order = {}
    for item in ITEMS:
        order[item[C]] = order.get(item[C], 0) + 1
        ChecklistItem.objects.get_or_create(category=item[C], title=item["title"], defaults={
            "arabic": item.get("arabic", ""), "translation": item.get("translation", ""),
            "reference": item.get("reference", ""), "order": order[item[C]]})
    for cat, titles in (("tajweed", TAJWEED), ("qiraat", QIRAAT), ("surah", SURAHS), ("namaz", NAMAZ)):
        for i, t in enumerate(titles, 1):
            ChecklistItem.objects.get_or_create(category=cat, title=t, defaults={"order": i})


class Migration(migrations.Migration):
    dependencies = [("hifz", "0002_checklistitem_qaidalesson_alter_juzprogress_options_and_more")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
