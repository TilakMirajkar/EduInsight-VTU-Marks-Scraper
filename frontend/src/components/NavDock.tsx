import { ArrowBigDownDash, ChartPie } from "lucide-react";
import { FloatingDock } from "./ui/floating-dock";

export function FloatingDockDemo() {
    const links = [
      {
        title: "Fetch Marks",
        icon: (
          <ArrowBigDownDash className="h-full w-full text-black dark:text-neutral-300" />
        ),
        href: "#",
      },
      {
        title: "Analyze",
        icon: (
          <ChartPie className="h-full w-full text-black dark:text-neutral-300" />
        ),
        href: "#",
      },
    ];
    return (
      <div>
        <FloatingDock
          items={links}
          direction="bottom"
        />
      </div>
    );
  }