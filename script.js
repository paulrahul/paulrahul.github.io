const body = document.body

const btnTheme = document.querySelector('.fa-moon')
const btnHamburger = document.querySelector('.fa-bars')

const addThemeClass = (bodyClass, btnClass) => {
  body.classList.add(bodyClass)
  if (btnTheme) btnTheme.classList.add(btnClass)
}

const getTheme = () => localStorage.getItem('portfolio-theme')

const saveTheme = (bodyClass, btnClass) => {
	localStorage.setItem('portfolio-theme', bodyClass)
	localStorage.setItem('portfolio-btn-theme', btnClass)
}

const isDark = () => body.classList.contains('dark')

const setTheme = (bodyClass, btnClass) => {
	body.classList.remove('theme-ocean-sand', 'dark')
	if (btnTheme) {
		btnTheme.classList.remove('fa-moon', 'fa-sun')
	}

	addThemeClass(bodyClass, btnClass)
	saveTheme(bodyClass, btnClass)
}

const toggleTheme = () =>
	isDark() ? setTheme('theme-ocean-sand', 'fa-moon') : setTheme('dark', 'fa-sun')

const currentTheme = getTheme()
const currentBtnTheme = localStorage.getItem('portfolio-btn-theme')

if (currentTheme) {
	body.classList.remove('theme-ocean-sand')
	addThemeClass(currentTheme, currentBtnTheme)
}

if (btnTheme) btnTheme.addEventListener('click', toggleTheme)

const displayList = () => {
	const navUl = document.querySelector('.nav__list')

	if (btnHamburger.classList.contains('fa-bars')) {
		btnHamburger.classList.remove('fa-bars')
		btnHamburger.classList.add('fa-times')
		navUl.classList.add('display-nav-list')
	} else {
		btnHamburger.classList.remove('fa-times')
		btnHamburger.classList.add('fa-bars')
		navUl.classList.remove('display-nav-list')
	}

	console.log(navUl);
}

btnHamburger.addEventListener('click', displayList)

const scrollUp = () => {
	const btnScrollTop = document.querySelector('.scroll-top')

	if (
		body.scrollTop > 500 ||
		document.documentElement.scrollTop > 500
	) {
		btnScrollTop.style.display = 'block'
	} else {
		btnScrollTop.style.display = 'none'
	}
}

document.addEventListener('scroll', scrollUp)

function createEl(tag, className, text) {
	const el = document.createElement(tag);
	if (className) el.className = className;
	if (text) el.textContent = text;
	return el;
}

let activeTags = new Set();

function linkify(text) {
	const urlRegex = /(https?:\/\/[^\s]+)/g;

	return text.replace(urlRegex, url => {
	  return `<a href="${url}" class="link" target="_blank" rel="noopener noreferrer">${url}</a>`;
	});
}

function renderProjects() {
	const grid = document.querySelector(".projects__grid");
	if (!grid) return;

	grid.innerHTML = "";

	const filtered = activeTags.size === 0
	? projectsData
	: projectsData.filter(project => {
		const searchable = [
		  ...(project.tags || []),
		  ...(project.stack || [])
		].map(item => item.toLowerCase());

		return [...activeTags].some(tag =>
		  searchable.includes(tag.toLowerCase())
		);
	});

	filtered.forEach(project => {
	  const projectDiv = createEl("div", "project");
	  projectDiv.tabIndex = 0;

	  /* ---------- project__content ---------- */
	  const content = createEl("div", "project__content");

	  const h4 = createEl("h4", null, project.title);

	  const figure = createEl("figure", "image is-3by2");
	  if (project.image) {
		const img = document.createElement("img");
		img.src = project.image;
	  //   if (project.imageFit) {
	  // 	img.style.objectFit = project.imageFit;
	  //   }
		img.style.objectFit = "contain";
		figure.appendChild(img);
	  }

	  const h5 = createEl("h5", null, project.tagline);

	  const tagsContainer = createEl("div", "project__tags");
	  if (project.tags) {
		project.tags.forEach(tag => {
		  const tagSpan = createEl("span", "project__tag", tag);
		  tagSpan.addEventListener("click", (e) => {
			e.stopPropagation();
			toggleTag(tag);
		  });

		  tagsContainer.appendChild(tagSpan);
		});
	  }

	  const stackUl = createEl("ul", "project__stack");
	  project.stack.forEach(tech => {
		const stackSpan = createEl("li", "project__stack-item", tech);
		stackSpan.addEventListener("click", (e) => {
			e.stopPropagation();
			toggleTag(tech.toLowerCase());
		});

		stackUl.appendChild(stackSpan);
	  });

	  content.append(h4, figure, h5, tagsContainer, stackUl);

	  const linksContainer = createEl("div", "project__links");
	  if (project.sourceUrl) {
		const sourceLink = document.createElement("a");
		sourceLink.href = project.sourceUrl;
		sourceLink.className = "link link--icon";
		sourceLink.setAttribute("aria-label", "source code");
		sourceLink.innerHTML = `<i class="fab fa-github"></i>`;
		linksContainer.appendChild(sourceLink);
	  }

	  if (project.liveUrl) {
		const liveLink = document.createElement("a");
		liveLink.href = project.liveUrl;
		liveLink.className = "link link--icon";
		liveLink.target = "_blank";
		liveLink.rel = "noopener noreferrer";
		liveLink.setAttribute("aria-label", "live preview");
		liveLink.innerHTML = `<i class="fas fa-external-link-alt"></i>`;

		linksContainer.appendChild(liveLink);
	  }
	  content.append(linksContainer);

	  /* ---------- project__alt-content ---------- */
	  const alt = createEl("div", "project__alt-content");
	  alt.hidden = true;

	  if (Array.isArray(project.description)) {
		const ul = document.createElement("ul");

		project.description.forEach(item => {
		  const li = document.createElement("li");
		  li.innerHTML = linkify(item);
		  ul.appendChild(li);
		});

		alt.appendChild(ul);
	  } else {
		// fallback for legacy string descriptions
		const p = document.createElement("p");
		p.textContent = project.description;
		alt.appendChild(p);
	  }

	  projectDiv.append(content, alt);
	  projectDiv.addEventListener("click", (e) => {
		// Ignore clicks on links (or inside links)
		if (e.target.closest("a")) return;

		projectDiv.classList.toggle("is-expanded");
	  });

	  grid.appendChild(projectDiv);
	});
}

function renderSkills(skills) {
	const ul = document.querySelector(".skills__list");
	if (!ul) return;

	skills.forEach(skill => {
	  const li = document.createElement("li");
	  li.className = "skills__list-item btn btn--plain";
	  li.textContent = skill;
	  ul.appendChild(li);
	});
}

function renderActiveTags() {
	const container = document.querySelector(".active-filters");
	container.innerHTML = "";

	activeTags.forEach(tag => {
	  const el = document.createElement("div");
	  el.className = "active-filter";
	  el.innerHTML = `${tag} <span>✕</span>`;

	  el.onclick = () => {
		activeTags.delete(tag);
		updateUI();
	  };

	  container.appendChild(el);
	});
}

function toggleTag(tag) {
	if (activeTags.has(tag)) {
	  activeTags.delete(tag);
	} else {
	  activeTags.add(tag);
	}
	updateUI();
	document.getElementById('projects').scrollIntoView({ behavior: 'smooth' });
}

function renderExperience() {
	const container = document.querySelector(".experience__list");
	if (!container) return;

	container.innerHTML = "";

	const filtered = activeTags.size === 0
	? experienceData
	: experienceData.filter(e => e.tags.some(tag =>
		activeTags.has(tag.toLowerCase()))
	);

	filtered.forEach(exp => {
	  const card = document.createElement("div");
	  card.className = "experience__card";

	  // Header
	  const header = document.createElement("div");
	  header.className = "experience__header";

	  const logo = document.createElement("div");
	  logo.className = "experience__logo";
	  logo.innerHTML = `<img src="${exp.logo}" alt="${exp.company} logo">`;

	  const meta = document.createElement("div");
	  meta.className = "experience__meta";

	  const title = document.createElement("h4");
	  title.textContent = exp.company;
	  const location = document.createElement("h5");
	  location.textContent = exp.location;

	  const subtitle = document.createElement("p");
	  subtitle.className = "experience__role";
	  subtitle.textContent = `${exp.role} — ${exp.start} to ${exp.end}`;

	  meta.append(title, location, subtitle);
	  header.append(logo, meta);

	  // Content
	  const content = document.createElement("div");
	  content.className = "experience__content";

	  const desc = document.createElement("p");
	  desc.textContent = exp.description;

	  const list = document.createElement("ul");
	  exp.achievements.forEach(item => {
		const li = document.createElement("li");
		li.innerHTML = linkify(item);
		list.appendChild(li);
	  });

	  const tags = document.createElement("div");
	  tags.className = "experience__tags";

	  exp.tags.forEach(tag => {
		const span = document.createElement("span");
		span.className = "experience__tag";
		span.textContent = tag;

		span.addEventListener("click", (e) => {
			e.stopPropagation();
			toggleTag(tag.toLowerCase());
			document.getElementById('experience').scrollIntoView({ behavior: 'smooth' });
		});

		tags.appendChild(span);
	  });

	  content.append(desc, list, tags);

	//   content.append(desc, list);
	  card.append(header, content);
	  container.appendChild(card);
	});
}

function updateUI() {
	renderActiveTags();
	renderProjects();
	renderExperience();
}

document.addEventListener("DOMContentLoaded", () => {
	updateUI();

	renderSkills(skillsData);

	document.querySelectorAll(".link--value").forEach(link => {
		link.addEventListener("click", (e) => {
		  e.preventDefault();     // stop navigation

		  const tag = e.target.textContent.trim();
		  toggleTag(tag.toLowerCase());
		});
	});
});