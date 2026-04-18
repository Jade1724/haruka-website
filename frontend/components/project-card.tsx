"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  GithubLogo,
  ArrowSquareOut,
  Link as LinkIcon,
} from "@phosphor-icons/react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
  type CarouselApi,
} from "@/components/ui/carousel";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ProjectLink = { type: string; url: string };
type ProjectImage = { id: string; altText: string };

type ProjectCardProps = {
  title: string;
  links: ProjectLink[];
  images: ProjectImage[];
  imagePos: "first" | "last";
  children: React.ReactNode;
};

function linkIcon(type: string) {
  switch (type.toLowerCase()) {
    case "github":
      return <GithubLogo size={14} />;
    case "live":
    case "demo":
      return <ArrowSquareOut size={14} />;
    default:
      return <LinkIcon size={14} />;
  }
}

function ProjectCarousel({ images }: { images: ProjectImage[] }) {
  const [api, setApi] = useState<CarouselApi>();
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!api) return;
    setCurrent(api.selectedScrollSnap());
    api.on("select", () => setCurrent(api.selectedScrollSnap()));
  }, [api]);

  return (
    <div className="flex flex-col gap-3">
      <Carousel setApi={setApi} opts={{ loop: true }}>
        <div className="relative aspect-video w-full overflow-hidden bg-muted">
          <CarouselContent className="-ml-0 h-full">
            {images.map((img) => (
              <CarouselItem key={img.id} className="pl-0">
                <div className="relative h-full w-full">
                  <Image
                    src={img.id}
                    alt={img.altText}
                    fill
                    className="object-cover"
                  />
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>

          {images.length > 1 && (
            <>
              <CarouselPrevious className="left-2 bg-background/70 backdrop-blur-sm hover:bg-background/90" />
              <CarouselNext className="right-2 bg-background/70 backdrop-blur-sm hover:bg-background/90" />
            </>
          )}
        </div>
      </Carousel>

      {images.length > 1 && (
        <div className="flex justify-center gap-1.5">
          {images.map((img, i) => (
            <button
              key={img.id}
              onClick={() => api?.scrollTo(i)}
              aria-label={`Go to image ${i + 1}`}
              className={cn(
                "h-1.5 rounded-full transition-all duration-200",
                i === current
                  ? "w-4 bg-foreground"
                  : "w-1.5 bg-muted-foreground/40 hover:bg-muted-foreground/60"
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProjectCard({
  title,
  links,
  images,
  imagePos,
  children,
}: ProjectCardProps) {
  const carouselSection = (
    <div>
      <ProjectCarousel images={images} />
    </div>
  );

  const descriptionSection = (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <div className="flex flex-wrap gap-2">
          {links.map((link) => (
            <Link
              key={link.url}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="sm" className="gap-1.5">
                {linkIcon(link.type)}
                <span className="capitalize">{link.type}</span>
              </Button>
            </Link>
          ))}
        </div>
      </div>
      <div className="text-sm leading-relaxed text-muted-foreground">
        {children}
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 items-center gap-8 md:grid-cols-2">
      {imagePos === "first" ? (
        <>
          {carouselSection}
          {descriptionSection}
        </>
      ) : (
        <>
          {descriptionSection}
          {carouselSection}
        </>
      )}
    </div>
  );
}
