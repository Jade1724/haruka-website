import ProjectCard from "@/components/project-card";

const projects = [
  {
    title: "Haruka Website",
    imagePos: "first" as const,
    images: [
      { id: "/next.svg", altText: "Haruka website homepage" },
      { id: "/vercel.svg", altText: "Haruka website projects page" },
    ],
    links: [
      { type: "github", url: "https://github.com/Jade1724/haruka-website" },
      { type: "live", url: "https://haruka.dev" },
    ],
    description:
      "This portfolio website built with Next.js, Tailwind CSS, and FastAPI. Features a project showcase, career timeline, and a dev journal scraped from a private Obsidian repository.",
  },
  {
    title: "Dev Journal Scraper",
    imagePos: "last" as const,
    images: [
      { id: "/next.svg", altText: "Dev journal scraper dashboard" },
    ],
    links: [
      { type: "github", url: "https://github.com/Jade1724/journal-scraper" },
    ],
    description:
      "A Python tool that reads markdown files from a private Obsidian vault on GitHub, parses frontmatter and content, and exposes them through a REST API built with FastAPI.",
  },
  {
    title: "Task Manager CLI",
    imagePos: "first" as const,
    images: [
      { id: "/next.svg", altText: "Task manager CLI screenshot" },
      { id: "/vercel.svg", altText: "Task manager CLI help output" },
    ],
    links: [
      { type: "github", url: "https://github.com/Jade1724/task-cli" },
      { type: "demo", url: "https://asciinema.org" },
    ],
    description:
      "A terminal-based task manager written in Python with persistent JSON storage, priority levels, due dates, and coloured output. Installable as a global CLI via pipx.",
  },
];

export default function ProjectsPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-12 text-2xl font-semibold">Projects</h1>
      <div className="flex flex-col gap-20">
        {projects.map((project) => (
          <ProjectCard
            key={project.title}
            title={project.title}
            imagePos={project.imagePos}
            images={project.images}
            links={project.links}
          >
            {project.description}
          </ProjectCard>
        ))}
      </div>
    </div>
  );
}
