import ProjectCard from "@/components/project-card";
import content from "@/lib/content.json";
import type { ProjectType } from "@/types/project";

export default function ProjectsPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-12 text-2xl font-semibold">Projects</h1>
      <div className="flex flex-col gap-20">
        {content.projects.map((project, i) => (
          <div key={project.title} className="flex flex-col gap-8">
            {i > 0 && <hr className="border-border md:hidden" />}
            <ProjectCard
              title={project.title}
              projectType={project.projectType as ProjectType}
              imagePos={project.imagePos as "first" | "last"}
              images={project.images}
              links={project.links}
            >
              {project.description}
            </ProjectCard>
          </div>
        ))}
      </div>
    </div>
  );
}
