"use client";

import { Moon, Sun } from "@phosphor-icons/react";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/components/theme-provider";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className="flex items-center gap-2">
      <Sun
        size={16}
        weight={!isDark ? "fill" : "regular"}
        className={!isDark ? "text-foreground" : "text-muted-foreground"}
      />
      <Switch
        checked={isDark}
        onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
        aria-label="Toggle dark mode"
      />
      <Moon
        size={16}
        weight={isDark ? "fill" : "regular"}
        className={isDark ? "text-foreground" : "text-muted-foreground"}
      />
      
    </div>
  );
}
