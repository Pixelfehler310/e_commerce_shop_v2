document.addEventListener("DOMContentLoaded", () => {
  const mermaidApi = window.mermaid;

  if (!mermaidApi || document.querySelectorAll(".mermaid").length === 0) {
    return;
  }

  mermaidApi.initialize({
    startOnLoad: true,
    securityLevel: "loose",
    theme: "base",
    themeVariables: {
      primaryColor: "#eef3ef",
      primaryTextColor: "#16211d",
      primaryBorderColor: "#136f63",
      lineColor: "#315c98",
      secondaryColor: "#ffffff",
      tertiaryColor: "#f5f7f4",
      fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }
  });

  mermaidApi.run({
    nodes: document.querySelectorAll(".mermaid")
  });
});