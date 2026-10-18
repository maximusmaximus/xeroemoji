export interface XeroEmoji { emoji: string; name: string; group: string; subgroup: string; file: string; key: string; order: number;
  codepoints: string; skinTone: string | null; svgUrl: string; pngUrl: string; svgPath: string; pngPath: string; }
export const VERSION: string;
export const LICENSE: string;
export function key(emoji: string): string;
export function get(query: string): XeroEmoji | null;
export function search(query: string, opts?: { group?: string; limit?: number; includeTones?: boolean }): XeroEmoji[];
export function variants(query: string): XeroEmoji[];
export function categories(): { group: string; count: number; subgroups: Record<string, number> }[];
export function url(query: string, format?: 'svg' | 'png'): string | null;
export function setBase(base: string): void;
export function map(): Record<string, [string, string, string, string, string, number]>;
