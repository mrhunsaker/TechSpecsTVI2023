TechSpecsTVI2023/ACCESSIBILITY_AUDIT.md
# Accessibility Audit: LaTeX Tagged PDF & PDF/UA Best Practices

This audit reviews each `.tex` file in the project for adherence to LaTeX accessibility best practices, focusing on PDF/UA compliance, semantic tagging, and the use of the `tagpdf` and related packages. The audit highlights strengths, identifies gaps, and provides recommendations for improvement.

---

## Audit Legend

- ✅ **Compliant**: Follows best practices for accessible, tagged PDFs.
- ⚠️ **Partial**: Some best practices are followed, but improvements are needed.
- ❌ **Missing**: Key accessibility features are absent.

---

## main.tex

**Summary:**  
This is the main entry point for the document and sets up global accessibility features.

- ✅ Uses `\DocumentMetadata` with `pdfstandard = ua-2` and `tagging=on`.
- ✅ Loads `tagpdf`, `accsupp`, and `hyperref` with Unicode and color options.
- ✅ Sets up accessible fonts (Atkinson Hyperlegible, APHont, OpenDyslexic, etc.).
- ✅ Defines `\imgalt` for accessible images using `\BeginAccSupp`.
- ✅ Configures table tagging and semantic structure.
- ✅ Sets document language (`lang = en-US`).
- ✅ Math accessibility enabled (`mathml-SE`).
- ✅ Suppresses optional PDF info for PDF/A compliance.
- ⚠️ **Recommendation:** Ensure all included images and tables in chapters use the defined accessible commands.

---

## Chapters/Chapter01.tex

**Summary:**  
Covers hardware limitations and screen reader performance.

- ✅ Uses semantic sectioning (`\chapter`, `\section`, etc.).
- ✅ Tables are tagged with `\tagpdfsetup{table/header-rows={1}}`.
- ✅ Uses `\imgalt` for at least one figure (screen reader load times).
- ⚠️ **Recommendation:** Ensure all figures use `\imgalt` and all tables are preceded by `\tagpdfsetup`.
- ⚠️ Check for alternative text on all images.

---

## Chapters/Chapter02.tex

**Summary:**  
Focuses on tablets and accessibility features.

- ✅ Semantic structure is present.
- ✅ Tables use `\tagpdfsetup{table/header-rows={1}}`.
- ⚠️ **Recommendation:** Ensure any images use `\imgalt` and have meaningful alt text.
- ⚠️ Confirm that all lists and tables are semantically tagged.

---

## Chapters/Chapter03.tex

**Summary:**  
Discusses braille displays and notetakers.

- ✅ Uses semantic sectioning.
- ✅ Tables are tagged for accessibility.
- ⚠️ **Recommendation:** If images are present, ensure `\imgalt` is used.
- ⚠️ Confirm all lists are semantically tagged.

---

## Chapters/Chapter04.tex

**Summary:**  
Covers braille embossers and tactile graphics.

- ✅ Semantic structure and table tagging are present.
- ⚠️ **Recommendation:** If tactile graphics or images are included, use `\imgalt` with descriptive alt text.
- ⚠️ Ensure all tables have header rows tagged.

---

## Chapters/Appendix1.tex

**Summary:**  
Troubleshooting for screen readers and magnifiers.

- ✅ Uses semantic sectioning.
- ⚠️ **Partial:** No evidence of images, but if present, must use `\imgalt`.
- ⚠️ **Recommendation:** Ensure all lists and tables are tagged.

---

## Chapters/Appendix2.tex

**Summary:**  
Troubleshooting braille notetakers and displays.

- ✅ Semantic structure is present.
- ⚠️ **Partial:** No images detected in the sample, but if present, use `\imgalt`.
- ⚠️ **Recommendation:** Tag all tables and lists.

---

## Chapters/Appendix3.tex

**Summary:**  
Assistive technology considerations and assessments.

- ✅ Uses semantic sectioning.
- ⚠️ **Partial:** No images or tables in the sample, but if present, ensure accessibility tagging.
- ⚠️ **Recommendation:** Tag all lists and tables.

---

## Chapters/Appendix4.tex

**Summary:**  
Instructional programs and accessible curricula.

- ✅ Semantic structure is present.
- ⚠️ **Partial:** No images in the sample, but if present, use `\imgalt`.
- ⚠️ **Recommendation:** Tag all tables and lists.

---

## Chapters/Appendix5.tex

**Summary:**  
Accessible fonts and typography.

- ✅ Uses accessible font samples.
- ✅ Semantic structure is present.
- ⚠️ **Partial:** If images of fonts or glyphs are included, ensure `\imgalt` is used.
- ⚠️ **Recommendation:** Tag all tables and lists.

---

## Chapters/BackMatter.tex

**Summary:**  
Back matter and copyright.

- ✅ Semantic structure is present.
- ⚠️ **Partial:** No images or tables in the sample, but if present, ensure accessibility tagging.

---

## General Observations

- **Strengths:**
  - The project is well-configured for PDF/UA and tagged PDF output.
  - Semantic structure is consistently used.
  - Accessible fonts and color contrast are prioritized.
  - Table tagging and header row marking are present in most chapters.
  - The `\imgalt` command is defined for accessible images.

- **Areas for Improvement:**
  - **Consistent Use of `\imgalt`:** Ensure every image uses this command with meaningful alt text.
  - **List Tagging:** Confirm that all `itemize` and `enumerate` lists are tagged for accessibility.
  - **Table Tagging:** All tables should be preceded by `\tagpdfsetup{table/header-rows={1}}`.
  - **Math Accessibility:** Confirm that all math is exported as MathML and is accessible in the output PDF.
  - **Avoid Manual Formatting:** Do not use raw formatting that bypasses semantic tagging.

---

## Recommendations

1. **Run a PDF/UA checker** (such as PAC 3 or Adobe Acrobat's accessibility checker) on the output PDF to verify compliance.
2. **Test with a screen reader** (NVDA, JAWS, or VoiceOver) to ensure all content is navigable and alt text is read correctly.
3. **Review all images and tables** in every chapter to confirm they use the defined accessibility commands.
4. **Document accessibility practices** in a CONTRIBUTING or README file for future contributors.

---

## Conclusion

Your project demonstrates strong commitment to LaTeX accessibility and tagged PDF best practices. With minor improvements in consistent tagging and alternative text, it will be exemplary for accessible PDF production.

---