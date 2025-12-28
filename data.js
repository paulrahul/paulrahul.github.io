const projectsData = [
    {
      title: "sonicsense.space",
      image: "img/sonicsense.png",
      tagline: "Intelligent search and trends of personal music library",
      tags: ["ai", "music", "web"],
      stack: ["Python", "Go", "OpenAI", "Postgres"],
      liveUrl: "https://sonicsense.space/",
      description: [
        "Helps users explore trends and insights from their personal music library",
        "Allows intelligent search on your music library using AI",
        "E.g.: 'list slow French songs with female voice as lead' or 'song from Mali featuring a chorus'"
      ]
    },
    {
      title: "serendi.pt",
      tagline: "Find yourself in others' captures",
      image: "img/serendipt.png",
      tags: ["social", "photos", "web"],
      stack: ["Flutter", "Drift"],
      liveUrl: "https://serendi.pt/",
      description: [
        "Portal to search strangers’ photos where you appear accidentally.",
      ]
    },
    {
      title: "Nazarriya",
      image: "img/nr1.png",
      tagline: "Creating safe spaces for young men to grow, reflect, and redefine masculinity",
      tags: ["mobile", "femtech", "ai"],
      stack: ["Flutter", "MySQL", "FastAPI"],
      sourceUrl: "https://github.com/justuju-in/nazarriya",
      liveUrl: "https://appdistribution.firebase.dev/i/5fa8c408319e24c6",
      description: [
        "Nazarriya is a platform encouraging dialogue, curiosity, and change",
        "Let's young men and boys chat with a trained AI assistant to discuss intimate and complex issues around gender, sexuality and consent",
        "Submitted as part of Unicef's call for Femtech apps and selected till the technical round"
      ]
    },
    {
      title: "Tagl",
      image: "img/tagl.webp",
      tagline: "Organize your digital life",
      tags: ["mobile", "share", "social"],
      stack: ["Flutter", "Drift"],
      liveUrl: "https://tagl.redoxsoft.com/",
      description: [
        "Tagl combines the best of tags, files and folders to organise your digital assets.",
        "Meant to let you quickly tag and save shared links, documents, texts in the form of searchable and indexed files"
      ]
    },
    {
      title: "herlove.world",
      image: "img/herlove.png",
      tagline: "Celebrating maternal love worldwide",
      tags: ["web", "social"],
      stack: ["TypeScript", "React"],
      liveUrl: "https://herlove.world",
      description:
        "Herlove.world celebrates maternal love across cultures and countries."
    },
    {
      title: "HaNe",
      image: "img/hane.jpg",
      tagline: "Utility Chrome extension for Hacker News",
      tags: ["extension", "tool", "hackernews"],
      stack: ["Chromium", "Javascript"],
      sourceUrl: "https://github.com/paulrahul/hane",
      liveUrl: "https://chromewebstore.google.com/detail/cdopgikfgbbbabbpcbokpbjiikikanfb?utm_source=item-share-cb",
      description: [
        "Extension that helps get a quick overview of what the Hacker News is saying about a particular web article/link",
        "Complemented with a Telegram bot: https://reorientinglife.substack.com/p/optimizing-my-hacker-news-experience",
        "Published in Hacker News with great reception: https://news.ycombinator.com/item?id=43927794"
      ]
    },
    {
      title: "Loopcart",
      image: "img/loopcart.png",
      tagline: "Smart, repeatable lists",
      tags: ["web", "privacy", "spa", "tool"],
      stack: ["Javascript", "Google Drive"],
      liveUrl: "https://loopcart-omega.vercel.app/",
      description:
        "Single-page, fully private app to help you view, sort and repeat your various lists in a smart way."
    },
    {
      title: "pipli",
      tagline: "Auto install pip dependencies",
      tags: ["tool", "cli"],
      stack: ["python"],
      liveUrl: "https://pypi.org/project/pipli/",
      description:
        "Auto install pip dependencies needed for a given command to run successfully."
    }
];

const skillsData = [
  "Python", "Go", "Javascript", "Dart",
  "React", "HTML", "CSS",
  "PostgreSQL", "MySQL",
  "RAG", "MCP", "Skills", "Claude Code", "Cursor",
  "Google Cloud", "Hetzner", "Git", "Docker"
];

const experienceData = [
  {
    role: "On a break",
    start: "Feb 2024",
    end: "present",
    logo: "https://upload.wikimedia.org/wikipedia/commons/6/66/Deepin_Icon_Theme_%E2%80%93_chronometer-pause.svg",
    description:
      "Upskilling (technical and cultural) and exploring new avenues.",
    achievements: [
      "Learnt mobile development and launched 2 apps",
      "Staying updated with AI developments and created a few AI based apps",
      "Learnt new dance forms and languages"
    ],
    tags: ["ai", "mobile", "flutter", "dance", "languages"]
  },
  {
    company: "Amazon (AWS Glue)",
    role: "Software Development Manager",
    start: "Jan 2023",
    end: "Jan 2024",
    location: "Berlin, Germany",
    logo: "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg",
    description:
      "Led core backend orchestration initiatives for AWS Glue and drove platform scalability.",
    achievements: [
      "Evaluated and scaled AWS Glue’s orchestration layer",
      "Led successful deprecation of AWS Data Pipeline (DPL)",
      "Led initial designs for Job Run Queueing"
    ],
    tags: ["AWS", "Distributed Systems", "Leadership", "Backend"]
  },
  {
    company: "Nutanix",
    role: "Director of Engineering",
    start: "Nov 2020",
    end: "Dec 2022",
    location: "Berlin, Germany",
    logo: "https://upload.wikimedia.org/wikipedia/commons/e/ea/Nutanix_Logo.svg",
    description:
      "Led multiple infrastructure teams and strategic cloud initiatives across geographies.",
    achievements: [
      "Led Nutanix Cloud (Xi) Infrastructure initiatives",
      "Managed 5–7 engineers across Berlin & US",
      "Drove Config Service, IP Management, Mini-DC & automation projects",
      "Contributed to hiring, culture, and org growth"
    ],
    tags: ["Leadership", "Cloud", "Infrastructure", "Kubernetes"]
  },
  {
    company: "Nutanix",
    role: "Senior Engineering Manager",
    start: "Aug 2019",
    end: "Oct 2020",
    location: "Berlin, Germany",
    logo: "https://upload.wikimedia.org/wikipedia/commons/e/ea/Nutanix_Logo.svg",
    description:
      "Built and scaled teams delivering cloud infrastructure services.",
    achievements: [
      "Started and led distributed Xi Cloud engineering team",
      "Oversaw planning, design, code reviews, and delivery",
      "Hands-on development in Python and Golang"
    ],
    tags: ["Engineering Management", "Cloud", "Python", "Golang"]
  },
  {
    company: "Nutanix",
    role: "Engineering Manager",
    start: "Jun 2017",
    end: "Jul 2019",
    location: "Bangalore, India",
    logo: "https://upload.wikimedia.org/wikipedia/commons/e/ea/Nutanix_Logo.svg",
    description:
      "Led Acropolis VM Control Plane team and expanded ownership across hypervisor services.",
    achievements: [
      "Scaled team from 10 to 22 engineers",
      "Delivered key features: UEFI, Auditing, Unified Publisher",
      "Maintained one of the highest-rated teams internally"
    ],
    tags: ["Distributed Systems", "Leadership", "Virtualization"]
  },
  {
    company: "Nutanix",
    role: "Staff Engineer",
    start: "Aug 2016",
    end: "Jul 2017",
    location: "Bangalore, India",
    logo: "https://upload.wikimedia.org/wikipedia/commons/e/ea/Nutanix_Logo.svg",
    description:
      "Technical lead for Uhura platform and DevOps adoption.",
    achievements: [
      "Expanded Uhura platform across multiple services",
      "Introduced DevOps and automation practices",
      "Led multi-threaded backend development"
    ],
    tags: ["Python", "DevOps", "Architecture"]
  },
  {
    company: "Nutanix",
    role: "Senior Member of Technical Staff",
    start: "Oct 2013",
    end: "Jul 2017",
    location: "Bangalore, India",
    logo: "https://upload.wikimedia.org/wikipedia/commons/e/ea/Nutanix_Logo.svg",
    description:
      "Founding engineer for multiple internal platforms and core systems.",
    achievements: [
      "Founded Uhura VM management system",
      "Led IDF database platform development",
      "Built automation and API generation frameworks"
    ],
    tags: ["C++", "Python", "Distributed Systems"]
  },
  {
    company: "Google",
    role: "Software Engineer",
    start: "Aug 2010",
    end: "Mar 2013",
    location: "Hyderabad, India",
    logo: "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
    description:
      "Worked on Google Workspace backend services and internal tools.",
    achievements: [
      "Developed Admin Audit Logs for Google Workspace",
      "Worked with BigTable, MapReduce, Protocol Buffers",
      "Trainer for internal Google technologies"
    ],
    tags: ["C++", "BigTable", "Distributed Systems"]
  }
];

