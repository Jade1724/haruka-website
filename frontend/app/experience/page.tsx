import ExperienceCard from "@/components/experience-card";

const experiences = [
  {
    title: "Software Engineer",
    startYear: 2023,
    endYear: null,
    organisation: {
      name: "Acme Corp",
      logo: { id: "/next.svg", altText: "Acme Corp logo" },
      link: "https://acme.com",
    },
    description:
      "Developed and maintained full-stack features across the platform using React, TypeScript, and Python. Led the migration of legacy REST endpoints to a GraphQL API, reducing over-fetching by 40%.",
  },
  {
    title: "Junior Frontend Developer",
    startYear: 2021,
    endYear: 2023,
    organisation: {
      name: "Bright Labs",
      logo: { id: "/vercel.svg", altText: "Bright Labs logo" },
      link: "https://brightlabs.io",
    },
    description:
      "Built responsive UI components and design system primitives in React. Collaborated closely with designers to implement pixel-perfect interfaces and improved Lighthouse performance scores from 62 to 94.",
  },
  {
    title: "Web Development Intern",
    startYear: 2020,
    endYear: 2021,
    organisation: {
      name: "Startup House",
      logo: { id: "/next.svg", altText: "Startup House logo" },
    },
    description:
      "Assisted in building internal tooling with Vue.js and Django. Wrote automated tests that reduced regression bugs by 30% ahead of each release cycle.",
  },
];

const education = [
  {
    title: "B.Sc. Computer Science",
    startYear: 2017,
    endYear: 2021,
    organisation: {
      name: "University of Melbourne",
      logo: { id: "/vercel.svg", altText: "University of Melbourne logo" },
      link: "https://unimelb.edu.au",
    },
    description:
      "Majored in software systems and artificial intelligence. Completed a capstone project on distributed task scheduling. Graduated with first-class honours.",
  },
  {
    title: "Exchange Program — Computer Science",
    startYear: 2019,
    endYear: 2020,
    organisation: {
      name: "ETH Zürich",
      logo: { id: "/next.svg", altText: "ETH Zürich logo" },
      link: "https://ethz.ch",
    },
    description:
      "One-year exchange focusing on algorithms, formal methods, and distributed systems. Studied in an international cohort and contributed to an open-source research compiler.",
  },
];

export default function ExperiencePage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-12 text-2xl font-semibold">Experience</h1>

      <section className="mb-16">
        <h2 className="mb-8 text-lg font-semibold text-muted-foreground">
          Work
        </h2>
        <div className="flex flex-col gap-8">
          {experiences.map((exp) => (
            <ExperienceCard key={exp.title} {...exp} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-lg font-semibold text-muted-foreground">
          Education
        </h2>
        <div className="flex flex-col gap-8">
          {education.map((edu) => (
            <ExperienceCard key={edu.title} {...edu} />
          ))}
        </div>
      </section>
    </div>
  );
}
