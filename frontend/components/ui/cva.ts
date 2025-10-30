type VariantConfig = {
  variants: Record<string, Record<string, string>>;
  defaultVariants?: Record<string, string>;
};

export function cva(base: string, config: VariantConfig) {
  return function (options?: Record<string, string | undefined>): string {
    const classes = [base];
    const variants = config.variants || {};
    const defaults = config.defaultVariants || {};
    for (const key of Object.keys(variants)) {
      const val = options?.[key] || defaults[key];
      if (val && variants[key][val]) classes.push(variants[key][val]);
    }
    const extra = options?.className;
    if (extra) classes.push(String(extra));
    return classes.join(" ");
  };
}
