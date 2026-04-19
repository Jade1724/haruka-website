import Image from "next/image";
import Link from "next/link";

type ExperienceCardProps = {
  title: string;
  startYear: number;
  endYear?: number | null;
  description: string;
  organisation: {
    name: string;
    logo: { id: string; altText: string };
    link?: string;
  };
};

export default function ExperienceCard({
  title,
  startYear,
  endYear,
  description,
  organisation,
}: ExperienceCardProps) {
  const yearRange = `${startYear} – ${endYear ?? "Current"}`;

  const orgName = (
    <span className="text-sm font-medium text-foreground">
      {organisation.name}
    </span>
  );

  return (
    <div className="flex flex-col gap-3 border-l-2 border-border pl-5">
      <div className="flex items-center gap-2.5">
        <div className="relative size-7 shrink-0 overflow-hidden rounded-sm bg-muted">
          <Image
            src={organisation.logo.id}
            alt={organisation.logo.altText}
            fill
            className="object-contain"
          />
        </div>
        {organisation.link ? (
          <Link
            href={organisation.link}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline underline-offset-4"
          >
            {orgName}
          </Link>
        ) : (
          orgName
        )}
      </div>

      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-xs text-muted-foreground">{yearRange}</p>
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
