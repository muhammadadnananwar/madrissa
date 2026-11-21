import {
  Award, BadgeCheck, BookMarked, BookOpen, Building2, Code2, Dumbbell, FlaskConical, GraduationCap, HandHeart, HeartHandshake,
  Landmark, Library, LifeBuoy, Lightbulb, Medal, MonitorSmartphone, PenTool, Presentation, ShieldCheck, Star, Trophy, Users, Sparkles,
  Globe2, Microscope, Music, Palette, Bus, Coffee, Wifi, Home,
} from 'lucide-react';

/** Icons available to editors (Admin > Settings "icon" fields use these names). */
export const ICONS = {
  Award, BadgeCheck, BookMarked, BookOpen, Building2, Code2, Dumbbell, FlaskConical, GraduationCap, HandHeart, HeartHandshake,
  Landmark, Library, LifeBuoy, Lightbulb, Medal, MonitorSmartphone, PenTool, Presentation, ShieldCheck, Star, Trophy, Users, Sparkles,
  Globe2, Microscope, Music, Palette, Bus, Coffee, Wifi, Home,
};

export const ICON_NAMES = Object.keys(ICONS);
export const getIcon = (name) => ICONS[name] || Sparkles;
