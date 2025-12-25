const body = document.body

const btnTheme = document.querySelector('.fa-moon')
const btnHamburger = document.querySelector('.fa-bars')

const addThemeClass = (bodyClass, btnClass) => {
  body.classList.add(bodyClass)
  btnTheme.classList.add(btnClass)
}

const getBodyTheme = localStorage.getItem('portfolio-theme')
const getBtnTheme = localStorage.getItem('portfolio-btn-theme')

addThemeClass(getBodyTheme, getBtnTheme)

const isDark = () => body.classList.contains('dark')

const setTheme = (bodyClass, btnClass) => {

	body.classList.remove(localStorage.getItem('portfolio-theme'))
	btnTheme.classList.remove(localStorage.getItem('portfolio-btn-theme'))

  addThemeClass(bodyClass, btnClass)

	localStorage.setItem('portfolio-theme', bodyClass)
	localStorage.setItem('portfolio-btn-theme', btnClass)
}

const toggleTheme = () =>
	isDark() ? setTheme('light', 'fa-moon') : setTheme('dark', 'fa-sun')

btnTheme.addEventListener('click', toggleTheme)

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

function renderProjects(projects) {
	const grid = document.querySelector(".projects__grid");
	if (!grid) return;

	projects.forEach(project => {
	  const projectDiv = createEl("div", "project");
	  projectDiv.tabIndex = 0;

	  /* ---------- project__content ---------- */
	  const content = createEl("div", "project__content");

	  const h4 = createEl("h4", null, project.title);

	  const figure = createEl("figure", "image is-3by2");
	  const img = document.createElement("img");
	  img.src = project.image;
	//   if (project.imageFit) {
	// 	img.style.objectFit = project.imageFit;
	//   }
	  img.style.objectFit = "contain";
	  figure.appendChild(img);

	  const h5 = createEl("h5", null, project.tagline);

	  const tagsContainer = createEl("div", "project__tags");
	  if (project.tags) {
		project.tags.forEach(tag => {
		  const tagSpan = createEl("span", "project__tag", tag);
		  tagsContainer.appendChild(tagSpan);
		});
	  }

	  const stackUl = createEl("ul", "project__stack");
	  project.stack.forEach(tech => {
		stackUl.appendChild(createEl("li", "project__stack-item", tech));
	  });

	  const sourceLink = document.createElement("a");
	  sourceLink.href = project.sourceUrl;
	  sourceLink.className = "link link--icon";
	  sourceLink.setAttribute("aria-label", "source code");
	  sourceLink.innerHTML = `<i class="fab fa-github"></i>`;

	  const liveLink = document.createElement("a");
	  liveLink.href = project.liveUrl;
	  liveLink.className = "link link--icon";
	  liveLink.setAttribute("aria-label", "live preview");
	  liveLink.innerHTML = `<i class="fas fa-external-link-alt"></i>`;

	  content.append(h4, figure, h5, tagsContainer, stackUl, sourceLink, liveLink);

	  /* ---------- project__alt-content ---------- */
	  const alt = createEl("div", "project__alt-content");
	  alt.hidden = true;

	  const p = createEl("p", null, project.description);
	  alt.appendChild(p);

	  projectDiv.append(content, alt);
	  projectDiv.addEventListener("click", (e) => {
		// Ignore clicks on links (or inside links)
		if (e.target.closest("a")) return;

		const isAltVisible = !alt.hasAttribute("hidden");

		if (isAltVisible) {
		  alt.setAttribute("hidden", "");
		  content.removeAttribute("hidden");
		} else {
		  content.setAttribute("hidden", "");
		  alt.removeAttribute("hidden");
		}
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

document.addEventListener("DOMContentLoaded", () => {
	renderProjects(projectsData);

	renderSkills(skillsData);
});