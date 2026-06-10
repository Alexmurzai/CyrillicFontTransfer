---
name: Obsidian Specimen
colors:
  surface: '#131314'
  surface-dim: '#131314'
  surface-bright: '#39393a'
  surface-container-lowest: '#0e0e0f'
  surface-container-low: '#1c1b1c'
  surface-container: '#201f20'
  surface-container-high: '#2a2a2b'
  surface-container-highest: '#353436'
  on-surface: '#e5e2e3'
  on-surface-variant: '#c7c4d8'
  inverse-surface: '#e5e2e3'
  inverse-on-surface: '#313031'
  outline: '#918fa1'
  outline-variant: '#464555'
  surface-tint: '#c4c0ff'
  primary: '#c4c0ff'
  on-primary: '#2000a4'
  primary-container: '#8781ff'
  on-primary-container: '#1b0091'
  inverse-primary: '#4f44e2'
  secondary: '#f5fff3'
  on-secondary: '#00391d'
  secondary-container: '#27ff97'
  on-secondary-container: '#00723f'
  tertiary: '#ffb785'
  on-tertiary: '#502500'
  tertiary-container: '#db761f'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c4c0ff'
  on-primary-fixed: '#100069'
  on-primary-fixed-variant: '#3622ca'
  secondary-fixed: '#5bffa1'
  secondary-fixed-dim: '#00e383'
  on-secondary-fixed: '#00210e'
  on-secondary-fixed-variant: '#00522c'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#131314'
  on-background: '#e5e2e3'
  surface-variant: '#353436'
  neon-violet: '#6C63FF'
  success-green: '#00FF94'
  deep-charcoal: '#0E0E0F'
  paper-white: '#F5F5F5'
  glass-border: rgba(255, 255, 255, 0.12)
typography:
  display-hero:
    fontFamily: anybody
    fontSize: 120px
    fontWeight: '900'
    lineHeight: 110px
    letterSpacing: -0.04em
  headline-xl:
    fontFamily: anybody
    fontSize: 64px
    fontWeight: '900'
    lineHeight: 72px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: anybody
    fontSize: 40px
    fontWeight: '900'
    lineHeight: 44px
    letterSpacing: -0.02em
  label-md:
    fontFamily: hankenGrotesk
    fontSize: 16px
    fontWeight: '300'
    lineHeight: 24px
    letterSpacing: 0.05em
  body-lg:
    fontFamily: hankenGrotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  functional-sm:
    fontFamily: jetbrainsMono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  grid-unit: 8px
  margin-safe: 48px
  gutter: 24px
  section-gap: 120px
---

## Brand & Style

This design system is a high-octane, professional typography engine aesthetic that prioritizes visual impact and editorial precision. Drawing inspiration from type foundries and technical documentation, the style is a hybrid of **High-Contrast Brutalism** and **Modern Glassmorphism**.

The brand personality is authoritative, sophisticated, and unapologetically bold. It targets designers, developers, and creative directors who value typographic hierarchy as a structural element rather than just content. The interface utilizes massive display type, asymmetric layouts, and "matte glass" surfaces to create a sense of depth and technical sophistication. The emotional response should be one of "industrial elegance"—where the raw power of typography meets the refined finish of a modern software interface.

## Colors

The palette is anchored in a true "Deep Charcoal" dark mode. This provides a high-contrast foundation for the "Neon Violet" primary accent, which serves as the signature color for interactions and focus states. 

- **Primary:** Neon Violet (#6C63FF) is used for active states, primary buttons, and critical UI highlights.
- **Success:** Neon Green (#00FF94) is reserved strictly for status indicators, positive progress, and valid inputs.
- **Neutral:** The background is #0E0E0F. Text and icons use high-contrast Paper White (#F5F5F5) or muted grays to ensure absolute legibility against the dark surfaces.
- **Surface Treatment:** Surfaces are defined by their opacity rather than lightness. Use semi-transparent layers for "matte glass" effects, allowing the deep background to remain visible through a heavy blur.

## Typography

Typography is the structural backbone of the design system. We utilize three distinct typefaces to separate hierarchy levels:

1.  **Display (Anybody):** A substitute for Calvino Grande Black. Used for massive, all-caps headers. It should be treated as a graphic element—often tightly tracked and overlapping container boundaries.
2.  **UI/Labels (Hanken Grotesk):** A substitute for Stratos Light. Used for mid-sized labels, navigation, and descriptors. Use the lighter weights (300) with generous letter spacing to provide a sophisticated, airy contrast to the heavy display type.
3.  **Functional (JetBrains Mono):** A substitute for Dotum. Used for metadata, technical specs, and small functional text. The monospaced nature adds to the "engine" aesthetic.

**Note:** For Display Hero sizes, ensure line height is tight (1.1) to create a "block" of text effect.

## Layout & Spacing

The layout follows an **Asymmetric Fixed Grid** model. While the content lives within a 12-column grid for desktop, elements should frequently break the grid or be positioned off-center to create visual tension.

- **Asymmetry:** Large type specimens should be left-aligned or even partially bled off-screen.
- **Vertical Spacing:** Use exaggerated vertical gaps (Section Gaps) to allow typography to breathe. 
- **Mobile Reflow:** On mobile, the 12-column grid collapses to 4 columns. Display type should scale aggressively (refer to `headline-xl-mobile`) to maintain the "type-first" impact on small screens.
- **Safe Areas:** Maintain a wide 48px margin on desktop to frame the content as if it were a high-end printed lookbook.

## Elevation & Depth

Depth is achieved through **Tonal Stacking and Glassmorphism** rather than traditional soft shadows.

1.  **Matte Glass Surfaces:** Use a background blur of 20px on containers with a semi-transparent fill (`rgba(20, 20, 22, 0.7)`).
2.  **High-Contrast Borders:** Every elevated panel must have a 2px solid border. Use `glass-border` for inactive states and `neon-violet` for active/hover states.
3.  **Neon Glows:** For active elements, use a "Neon Glow" instead of a shadow. This is an outer glow using the primary color (`#6C63FF`) with 0px offset, 15px blur, and 0.4 opacity.
4.  **No Drop Shadows:** Avoid traditional black shadows. Depth is communicated via the refraction of the backdrop blur and the sharpness of the container outlines.

## Shapes

The shape language is rigid and architectural. 

- **Corner Radius:** A consistent 4px radius is used across all UI components (buttons, input fields, cards). This "Soft" sharp corner maintains the professional, technical feel without the aggression of 0px corners.
- **Border Weight:** A mandatory 2px border is applied to all interactive containers. 
- **Specimen Boxes:** Large content blocks should utilize perfectly square corners (0px) to distinguish "content" from "UI."

## Components

- **Buttons:** Primary buttons feature a solid Neon Violet fill with Paper White text in JetBrains Mono (All-caps). Secondary buttons use a 2px Neon Violet border with no fill. On hover, apply the Neon Glow.
- **Input Fields:** 2px deep-charcoal-light border. When focused, the border transitions to Neon Violet and the background becomes slightly less transparent. Use JetBrains Mono for input text.
- **Cards (Matte Glass):** Containers use the 20px backdrop blur and 2px `glass-border`. Title text within cards should be Hanken Grotesk 300 with wide tracking.
- **Chips/Status:** Small JetBrains Mono text inside a container with a 1px border. Success states use Neon Green for both the text and the border.
- **Type Specimens:** Specialized components for displaying fonts. These should allow for "massive" font sizes that can span the full width of the grid, using the `display-hero` style.
- **Active States:** Anything "active" or "selected" should use a Neon Violet glow and a 2px border.