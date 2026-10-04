"""
A small hand-built list of Pakistani people, places and organizations that appear often in
2020-2021 English-language news. Used to check whether the concreteness pipeline's named-entity
step (spaCy en_core_web_sm after truecasing) recognizes local names.

Each entry: (surface form, type). Matching is case-insensitive and on whole words.
Extend this list freely; it is meant as a transparent starting point, not a complete inventory.
"""

PLACES = [
    "Pakistan", "Islamabad", "Lahore", "Karachi", "Rawalpindi", "Peshawar", "Quetta", "Multan",
    "Faisalabad", "Gujranwala", "Sialkot", "Hyderabad", "Sukkur", "Larkana", "Bahawalpur",
    "Bahawalnagar", "Sargodha", "Abbottabad", "Mardan", "Swat", "Gilgit", "Skardu", "Muzaffarabad",
    "Gwadar", "Turbat", "Dera Ghazi Khan", "Dera Ismail Khan", "Rahim Yar Khan", "Sheikhupura",
    "Kasur", "Jhelum", "Mirpur", "Chitral", "Waziristan", "North Waziristan", "South Waziristan",
    "Tharparkar", "Thar", "Punjab", "Sindh", "Balochistan", "Khyber Pakhtunkhwa", "KP", "KPK",
    "Gilgit-Baltistan", "Azad Kashmir", "AJK", "FATA", "Torkham", "Chaman", "Wagah",
]

ORGS = [
    "PTI", "PML-N", "PMLN", "PPP", "MQM", "MQM-P", "JUI-F", "JUI", "ANP", "BNP", "PDM", "TLP",
    "Jamaat-e-Islami", "NAB", "FIA", "FBR", "ECP", "SBP", "State Bank", "PCB", "ISPR", "NDMA",
    "NCOC", "PIA", "WAPDA", "NEPRA", "OGRA", "SECP", "PSX", "KSE", "HEC", "PEMRA", "PTA", "CDA",
    "LHC", "SHC", "IHC", "PHC", "Supreme Court", "Senate", "National Assembly", "CPEC", "PSL",
    "Lahore Qalandars", "Karachi Kings", "Islamabad United", "Peshawar Zalmi", "Quetta Gladiators",
    "Multan Sultans", "Dawn", "Geo", "ARY", "Express Tribune", "K-Electric", "Sui Southern",
]

PEOPLE = [
    "Imran Khan", "Nawaz Sharif", "Shehbaz Sharif", "Maryam Nawaz", "Hamza Shehbaz",
    "Bilawal Bhutto", "Bilawal Bhutto Zardari", "Bilawal", "Asif Zardari", "Asif Ali Zardari",
    "Fazlur Rehman", "Maulana Fazl", "Usman Buzdar", "Murad Ali Shah", "Mahmood Khan",
    "Jam Kamal", "Shah Mehmood Qureshi", "Asad Umar", "Hafeez Shaikh", "Shaukat Tarin",
    "Hammad Azhar", "Sheikh Rashid", "Fawad Chaudhry", "Shibli Faraz", "Shireen Mazari",
    "Faisal Sultan", "Zafar Mirza", "Yasmin Rashid", "Arif Alvi", "Qamar Javed Bajwa", "Bajwa",
    "Jahangir Tareen", "Pervez Elahi", "Khawaja Asif", "Ahsan Iqbal", "Shahid Khaqan Abbasi",
    "Gulzar Ahmed", "Qazi Faez Isa", "Babar Azam", "Mohammad Rizwan", "Shaheen Afridi",
    "Shahid Afridi", "Sarfaraz Ahmed", "Misbah-ul-Haq", "Misbah", "Waqar Younis", "Azhar Ali",
    "Fakhar Zaman", "Shoaib Akhtar", "Malala", "Mahira Khan",
]

GAZETTEER = ([(p, "GPE") for p in PLACES] + [(o, "ORG") for o in ORGS] + [(p, "PERSON") for p in PEOPLE])
