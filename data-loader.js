const dataUrl = new URL("./data.json", document.currentScript.src);

const validatePortfolioData = (data) => {
  if (
    !data ||
    !Array.isArray(data.projects) ||
    !data.skills ||
    typeof data.skills !== "object" ||
    !Array.isArray(data.experience)
  ) {
    throw new Error("data.json is missing one or more required portfolio sections.");
  }

  return data;
};

window.portfolioDataReady = fetch(dataUrl)
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Could not load portfolio data (${response.status}).`);
    }

    return response.json();
  })
  .then(validatePortfolioData)
  .then((data) => {
    window.projectsData = data.projects;
    window.skillsData = data.skills;
    window.experienceData = data.experience;
    return data;
  });

