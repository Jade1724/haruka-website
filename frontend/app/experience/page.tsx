import ExperienceCard from "@/components/experience-card";
import content from "@/lib/content.json";

export default function ExperiencePage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-12 text-2xl font-semibold">Experience</h1>

      <section className="mb-16">
        <h2 className="mb-8 text-lg font-semibold text-muted-foreground">
          Work
        </h2>
        <div className="flex flex-col gap-8">
          {content.work.map((exp) => (
            <ExperienceCard key={exp.title} {...exp} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-lg font-semibold text-muted-foreground">
          Education
        </h2>
        <div className="flex flex-col gap-8">
          {content.education.map((edu) => (
            <ExperienceCard key={edu.title} {...edu} />
          ))}
        </div>
      </section>
    </div>
  );
}
