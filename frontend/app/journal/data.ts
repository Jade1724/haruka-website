export type JournalEntry = {
  id: string;
  title: string;
  publishedOn: Date;
  updatedOn: Date;
  content: string;
};

export const journals: JournalEntry[] = [
  {
    id: "setting-up-nextjs-with-fastapi",
    title: "Setting up Next.js with a FastAPI backend",
    publishedOn: new Date("2024-11-03"),
    updatedOn: new Date("2024-11-05"),
    content: `Getting a Next.js frontend talking to a FastAPI backend turned out to be straightforward, but there were a few gotchas worth documenting.

The first issue was CORS. FastAPI doesn't enable it by default, so any fetch from the browser gets blocked immediately. Adding CORSMiddleware with the right origins fixed it. In development I allow everything, but I'm being explicit about origins in production.

The second issue was environment variables. Next.js only exposes variables prefixed with NEXT_PUBLIC_ to the browser. I burned 20 minutes wondering why my API URL was undefined before I remembered this.

For data fetching I'm using TanStack Query on the frontend. It handles caching, background refetching, and loading/error states cleanly. Pairing it with the Next.js experimental streaming support means I can start rendering pages before the data is fully loaded.

The backend is deployed as Vercel serverless functions. Cold starts are noticeable on the free tier but acceptable for a portfolio. If it becomes a problem I'll look at keeping the function warm with a scheduled ping.`,
  },
  {
    id: "tailwind-v4-migration",
    title: "What changed moving to Tailwind CSS v4",
    publishedOn: new Date("2024-11-18"),
    updatedOn: new Date("2024-11-18"),
    content: `Tailwind v4 is a significant departure from v3. Here is what actually affected my day-to-day workflow.

Configuration moved out of tailwind.config.js and into CSS. You define your theme inside @theme {} blocks directly in your stylesheet. This feels odd at first but removes a whole layer of indirection — the design tokens live next to the styles that use them.

The color system now uses oklch by default. This means interpolation between colors looks visually even rather than passing through muddy midpoints. The downside is that oklch values are not intuitive to write by hand, so I rely on the shadcn theme generator to produce them.

Arbitrary values still work the same way. Most of my utility classes migrated without changes.

The PostCSS plugin is now @tailwindcss/postcss instead of tailwindcss directly. This tripped up my build until I updated postcss.config.mjs.

Overall the migration took about two hours including updating the shadcn components to match the new config format. The resulting CSS bundle is noticeably smaller.`,
  },
  {
    id: "obsidian-github-scraper",
    title: "Scraping my Obsidian vault from GitHub",
    publishedOn: new Date("2024-12-01"),
    updatedOn: new Date("2024-12-09"),
    content: `My notes live in a private Obsidian vault synced to GitHub. The goal was to surface selected notes as journal entries on this site without making the whole vault public.

The approach: a FastAPI endpoint that calls the GitHub Contents API, fetches specific markdown files, parses the frontmatter with python-frontmatter, and returns structured JSON. The frontend never touches GitHub directly.

Frontmatter drives everything. Each note I want to publish has published: true set. The scraper filters on this field so I can keep drafts and private notes in the same vault without them leaking.

Rate limits were a concern. The GitHub API allows 5000 authenticated requests per hour, which is more than enough, but I added response caching on the FastAPI side so repeated page loads don't hit GitHub at all. Cache TTL is 10 minutes.

Markdown rendering on the frontend is next. I'm deciding between react-markdown and a server-side solution that converts to HTML before sending it down. Leaning toward the server-side option to keep the client bundle lighter.`,
  },
  {
    id: "embla-carousel-setup",
    title: "Building the project screenshot carousel with Embla",
    publishedOn: new Date("2025-01-14"),
    updatedOn: new Date("2025-01-14"),
    content: `The project cards on this site each have a screenshot carousel. I used Embla Carousel via the shadcn carousel component as the base.

The main customisation was positioning the previous and next buttons inside the image frame rather than outside it. The default shadcn styles place them at -left-12 and -right-12, which works when there is space around the carousel but breaks inside a constrained grid column. Overriding those classes to left-2 and right-2 with a semi-transparent background fixed it.

Dot indicators weren't part of the shadcn component out of the box. I used the setApi prop to get a reference to the Embla API, then listened to the select event to track the current index. Each dot is a plain button that calls api.scrollTo(i) on click.

One issue: the aspect-video container and Embla's overflow-hidden wrapper interact in a way that requires explicit height on the carousel content div. Without it the slides collapse to zero height. Setting h-full on both the content wrapper and each slide item resolved it.

I'm happy with how it turned out. The component is reusable, takes an images array, and hides the navigation controls entirely when there is only one image.`,
  },
];
