# Workshop definitions for easy management
# Add new workshops here and run: python workshop_manager.py add <workshop_key>

WORKSHOPS = {
    "byog": {
        "workshop_id": "byog-workshop",
        "title": "BYOG – Build Your Own Game",
        "description": "Ever wanted to build a video game without coding? BYOG is a beginner-friendly game design workshop and mini jam where participants learn core design concepts and create a playable game using a no-code engine.",
        "main_description": "BYOG is a hands-on game design workshop combined with a mini game jam. Participants are introduced to fundamental game design principles and guided through building a game using a no-code engine. After a live demonstration, participants enter a creative sprint to design and develop their own playable game prototype. The event focuses on creativity, gameplay design, and practical learning, ensuring every participant leaves with a functional game build",
        "rules": """• The event duration is 2 hours, consisting of a guided workshop followed by a creative game jam.
• Participants may work solo or in teams of 2–4 members.
• All projects must start from a new, blank project at the beginning of the event.
• Pre-made games or previously worked-on projects are not allowed.
• Participants may use free built-in assets or create simple custom assets.
• Focus should be on gameplay and mechanics, not just visuals.
• Judges will evaluate teams during the build phase based on creativity, clarity of mechanics, and implementation quality.
• Selected projects will be showcased briefly at the end of the event.
• Judges' and organizers' decisions are final and binding.""",
        "organisers": [
            {"name": "Thiruvel S", "phone": "+91 7539924705"},
            {"name": "vigneshwar P", "phone": "+91 63791 31591"}
        ],
        "instructor": "Thiruvel S & vigneshwar P",
        "date": "2026-03-25",
        "time": "2:00 PM",
        "duration": "2 Hours",
        "venue": "Game Design Lab",
        "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420",
        "max_participants": 50,
        "registration_fee": 300,
        "status": "open"
    },
    
    "cybersecurity": {
        "workshop_id": "cybersecurity-ai-workshop",
        "title": "Cybersecurity with AI Through Behavioural Analysis",
        "description": "From social media habits to login timing, learn how AI turns behavior into security intelligence. A powerful workshop experience combining technology, strategy, and real-world cyber awareness.",
        "main_description": "Modern cyber threats begin with understanding human behavior. This workshop explores how Artificial Intelligence uses behavioral analysis to predict attacks, detect anomalies, and protect digital identities. Through real-world cases, live AI demonstrations, and interactive discussions, participants gain practical insight into how intelligent cybersecurity systems defend against silent, evolving cyber threats.",
        "rules": """• The workshop is open to students from CSE, AI & DS, IT, and other related departments.
• Prior registration is mandatory; seats are limited and allotted on a first-come, first-served basis.
• Participants must attend the full workshop duration to receive certificates or attendance benefits.
• All participants should report to the venue at least 10 minutes before the session begins.
• Bringing a laptop is recommended for better hands-on understanding; mobile phones must be kept on silent mode.
• Participants must maintain discipline, professionalism, and respectful behavior throughout the workshop.
• Active interaction and questions are encouraged during discussions and demonstrations.
• Recording or photography is not permitted without prior permission from the organizers.
• Certificates (if applicable) will be issued only to participants who complete the full session.
• The organizers reserve the right to modify the schedule, structure, or rules when required.""",
        "organisers": [
            {"name": "Prabha", "phone": "7845386801", "role": "Lead"},
            {"name": "Surya Prasanna", "phone": "7708348815", "role": "Organizer"},
            {"name": "Heamapreyan", "phone": "8667470196", "role": "Organizer"}
        ],
        "instructor": "Prabha & Team",
        "date": "2026-03-28",
        "time": "10:00 AM",
        "duration": "3 Hours",
        "venue": "Cybersecurity Lab",
        "image_url": "https://images.unsplash.com/photo-1550751827-4bd3774c3f58",
        "max_participants": 60,
        "registration_fee": 400,
        "status": "open"
    },
    
    "blockchain": {
        "workshop_id": "blockchain-workshop",
        "title": "Inside a Blockchain: Transactions, Blocks & Hashes",
        "description": "Ever wondered what makes blockchain unhackable? Inside a Blockchain takes you beyond the buzzwords into hands-on exploration of transactions, blocks, and cryptographic hashes—where you'll manually build a mini blockchain and witness immutability in action.",
        "main_description": "Inside a Blockchain is a hands-on workshop where participants learn blockchain fundamentals through practical simulation. Starting with theory on transactions, blocks, and hashing, you'll progress to live demonstrations of SHA-256 hash generation and block linking. The core experience involves manually creating transactions, generating cryptographic hashes, building blocks, and linking them together. Finally, you'll test blockchain immutability by attempting to tamper with data—experiencing firsthand why blockchain is trusted and secure.",
        "rules": """Workshop Structure:
Session 1 - Theory (45 minutes): Introduction to transactions, blocks, hashing, and chain linking concepts
Session 2 - Live Demo (30 minutes): Real-time demonstration of hash generation and block linking
Session 3 - Hands-On Activity (60 minutes): Participants build a mini blockchain manually
Session 4 - Concept Reinforcement (15 minutes): Real-world applications and industry relevance
Session 5 - Wrap-Up & Q&A (20 minutes): Career insights and open discussion

Participation Rules:
• Open to all beginners and college students; no prior blockchain knowledge required
• Participants must bring laptops for hands-on activities
• Active participation in all sessions is mandatory for completion certificate
• Internet access required for live demonstrations and hash generation tools
• Note-taking is encouraged; workshop materials will be provided

Workshop Guidelines:
• Punctuality is essential; sessions are sequential and interconnected
• Respectful engagement during theory and demo sessions
• Collaborative learning is encouraged during hands-on activities
• Questions are welcome throughout the workshop
• Organizers' instructions must be followed for smooth coordination

Requirements:
• Laptop/computer with internet connectivity
• Note-taking materials
• Enthusiasm to learn blockchain fundamentals""",
        "organisers": [
            {"name": "Jayasoorya", "phone": "+91 70926 95703", "role": "Head"},
            {"name": "Madan Raj", "phone": "+91 88071 89438", "role": "Organiser"},
            {"name": "Akshayakumaran", "phone": "+91 9360432078", "role": "Organiser"}
        ],
        "instructor": "Jayasoorya & Team",
        "date": "2026-03-30",
        "time": "1:00 PM",
        "duration": "2.5 Hours",
        "venue": "Blockchain Lab",
        "image_url": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0",
        "max_participants": 50,
        "registration_fee": 350,
        "status": "open"
    },
    
    "snn": {
        "workshop_id": "snn-workshop",
        "title": "Spiking Neural Networks for Neuromorphic Systems",
        "description": "Ever wondered how computers could think like brains? This guide explores Spiking Neural Networks (SNNs)—energy-efficient, event-driven systems that process information using discrete pulses of electricity, mimicking biological intelligence for next-gen hardware.",
        "main_description": """Ever wondered how computers could think like brains? This guide explores Spiking Neural Networks (SNNs)—energy-efficient, event-driven systems that process information using discrete pulses of electricity, mimicking biological intelligence for next-gen hardware.

MODULE 1 — Why SNNs Exist
MODULE 2 — What a Spike Is
MODULE 3 — The Only Neuron You Need: LIF
MODULE 4 — Encoding
MODULE 5 — Minimal SNN Architecture
MODULE 6 — Learning in SNNs
MODULE 7 — Training vs. Inference
MODULE 8 — Practical SNN Thinking""",
        "organisers": [
            {"name": "Mithun Vimalan S.A", "phone": "9843629356"},
            {"name": "Nava Jyothi K.P", "phone": "7604897243"}
        ],
        "instructor": "Mithun Vimalan S.A & Nava Jyothi K.P",
        "date": "2026-04-02",
        "time": "11:00 AM",
        "duration": "3 Hours",
        "venue": "AI Research Lab",
        "image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995",
        "max_participants": 40,
        "registration_fee": 450,
        "status": "open"
    }
}
