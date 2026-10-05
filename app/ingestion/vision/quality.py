"""
Image Quality and Legibility Analyzer for myCA Vision Engine.
Evaluates:
- Low resolution
- Blur (low edge/Laplacian variance)
- Extreme glare / overexposure (high pixel luminance saturation)
- Extreme underexposure / darkness
- Low contrast
"""

import io
from PIL import Image, ImageFilter, ImageStat
from .models import ImageQualityAssessment

def assess_image_quality(image_bytes: bytes, filename: str = "") -> ImageQualityAssessment:
    """
    Evaluates raw image bytes for readability, focus, exposure, and resolution.
    Returns ImageQualityAssessment.
    """
    issues = []
    
    try:
        im = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return ImageQualityAssessment(
            is_acceptable=False,
            score=0.0,
            issues=["CORRUPTED_IMAGE"],
            message="Ye image open nahi ho rahi. File corrupted ho sakti hai."
        )

    width, height = im.size
    
    # 1. Resolution Check
    if width < 150 or height < 150:
        issues.append("LOW_RESOLUTION")

    # Convert to grayscale for illumination & edge analysis
    gray = im.convert("L")
    stat = ImageStat.Stat(gray)
    mean_lum = stat.mean[0]
    lum_var = stat.var[0]

    # 2. Extreme Glare / Overexposure
    if mean_lum > 252.0 and lum_var < 5.0:
        issues.append("EXTREME_GLARE")

    # 3. Extreme Darkness / Underexposure
    if mean_lum < 15.0 and lum_var < 20.0:
        issues.append("EXTREME_DARKNESS")

    # 4. Blur / Out of focus detection
    lap_kernel = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)
    lap_img = gray.filter(lap_kernel)
    lap_var = ImageStat.Stat(lap_img).var[0]

    # Solid / empty check
    if lum_var < 1.0:
        if "EXTREME_GLARE" not in issues:
            issues.append("BLANK_IMAGE")
    elif lap_var < 100.0 and "EXTREME_GLARE" not in issues:
        issues.append("BLURRY_IMAGE")

    is_acceptable = len(issues) == 0
    score = 1.0 if is_acceptable else max(0.1, 1.0 - (len(issues) * 0.4))

    message = "Image quality is good for processing."
    if "BLURRY_IMAGE" in issues or "LOW_RESOLUTION" in issues:
        message = "Photo thodi unclear hai. Amount clearly read nahi ho raha. Kripya clear photo upload karein."
    elif "EXTREME_GLARE" in issues:
        message = "Photo par bahut zyada light/glare hai. Kripya bina glare ke photo upload karein."
    elif "EXTREME_DARKNESS" in issues:
        message = "Photo bahut dark hai. Kripya achhi lighting mein photo lein."
    elif "BLANK_IMAGE" in issues:
        message = "Ye photo khali ya blank lag rahi hai. Kripya valid document upload karein."

    return ImageQualityAssessment(
        is_acceptable=is_acceptable,
        score=score,
        issues=issues,
        message=message,
        blur_score=float(lap_var),
        glare_score=float(mean_lum)
    )
