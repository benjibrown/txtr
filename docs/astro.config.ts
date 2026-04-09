import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";
import hcStarlight from "hc-starlight";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://txtr.benji.mom",
  integrations: [
    react(),
    starlight({
      logo: {
          src: './src/assets/logo.svg',
        replacesTitle: true,
      },
      title: "txtr",
      description: "A Vim-style LaTeX editor for the terminal. LaTeX, fast.",
      favicon: "/favicon.svg",
      head: [
        { tag: "meta", attrs: { property: "og:type", content: "website" } },
        { tag: "meta", attrs: { property: "og:url", content: "https://txtr.benji.mom" } },
        { tag: "meta", attrs: { property: "og:title", content: "txtr" } },
        { tag: "meta", attrs: { property: "og:description", content: "A Vim-style LaTeX editor for the terminal. LaTeX, fast." } },
        { tag: "meta", attrs: { property: "og:image", content: "https://txtr.benji.mom/og.png" } },
        { tag: "meta", attrs: { name: "twitter:card", content: "summary_large_image" } },
        { tag: "meta", attrs: { name: "twitter:title", content: "txtr" } },
        { tag: "meta", attrs: { name: "twitter:description", content: "A Vim-style LaTeX editor for the terminal. LaTeX, fast." } },
        { tag: "meta", attrs: { name: "twitter:image", content: "https://txtr.benji.mom/og.png" } },
      ],
      components: {
        Hero: "./src/components/HeroWithBackground.astro",
      },
      plugins: [
        hcStarlight({
          hcSocial: [
            {
              icon: "github",
              href: "https://github.com/benjibrown/txtr",
              label: "GitHub",
            },
          ],
        }),
      ],
      sidebar: [
        {
          label: "Getting Started",
          items: [
            { label: "Introduction", slug: "introduction" },
            {label: "Installation", slug: "installation" },
            {label: "Quick Start", slug: "quickstart" },
          ],
        },
        {
          label: "Usage",
          items: [
            { label: "Modes", slug: "usage/modes" },
            { label: "Keybinds", slug: "usage/keybinds" },
            {label: "Commands", slug: "usage/commands" },
          ],
        },
      ],
    }),
  ],
});
