import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";
import hcStarlight from "hc-starlight";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://txtr.benji.mom",
  integrations: [
    react(),
    starlight({
      title: "txtr",
      description: "A Vim-style LaTeX editor for the terminal. LaTeX, fast.",
      editLink: {
        baseUrl: "https://github.com/benjibrown/txtr/edit/main/docs/",
      },
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
          ],
        },
      ],
    }),
  ],
});
