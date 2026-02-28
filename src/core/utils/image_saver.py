"""Image saver utility for pipeline debugging and visualization"""

import logging
from pathlib import Path
import numpy as np
import cv2
from typing import Optional, TYPE_CHECKING

from src.core.settings import settings
from src.core.enums import ProcessingStep

if TYPE_CHECKING:
    from src.components.processing.context import WindowProcessingContext

logger = logging.getLogger("logger")


class ImageSaver:
    """
    Saves intermediate images during window processing pipeline.
    
    Utility class with classmethods for stateless image saving.
    """
    
    @classmethod
    def save_df_values(
        cls,
        df_values: np.ndarray,
        window_id: str,
        step: str,
        step_number: int
    ) -> Optional[Path]:
        """
        Save DF values array as image.
        
        Args:
            df_values: DF values array (0-1 normalized)
            window_id: Window identifier
            step: Step name (e.g., 'standardized', 'rotated', 'cropped')
            step_number: Sequential step number
            
        Returns:
            Path to saved file or None if saving disabled
        """
        if not settings.SAVE_IMAGES:
            return None
            
        try:
            outputs_path = Path(settings.IMAGES_OUTPUT_DIR)
            outputs_path.mkdir(parents=True, exist_ok=True)
            
            # Normalize to 0-1 range, then to 0-255 for visualization
            df_min = np.min(df_values)
            df_max = np.max(df_values)
            if df_max > df_min:
                df_normalized_01 = (df_values - df_min) / (df_max - df_min)
            else:
                df_normalized_01 = np.zeros_like(df_values)
            df_normalized = (df_normalized_01 * 255).astype(np.uint8)
            
            filename = f"{step_number:02d}_{window_id}_{step}_df.png"
            filepath = outputs_path / filename
            
            cv2.imwrite(str(filepath), df_normalized)
            logger.debug(f"Saved DF image: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving DF image: {e}")
            return None
    
    @classmethod
    def save_mask(
        cls,
        mask: np.ndarray,
        window_id: str,
        step: str,
        step_number: int
    ) -> Optional[Path]:
        """
        Save mask array as image.
        
        Args:
            mask: Mask array (0/1 values)
            window_id: Window identifier
            step: Step name
            step_number: Sequential step number
            
        Returns:
            Path to saved file or None if saving disabled
        """
        if not settings.SAVE_IMAGES:
            return None
        
        try:
            outputs_path = Path(settings.IMAGES_OUTPUT_DIR)
            outputs_path.mkdir(parents=True, exist_ok=True)
            
            # Convert to 0-255 for visualization
            mask_visualization = (mask * 255).astype(np.uint8)
            
            filename = f"{step_number:02d}_{window_id}_{step}_mask.png"
            filepath = outputs_path / filename
            
            cv2.imwrite(str(filepath), mask_visualization)
            logger.debug(f"Saved mask image: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving mask image: {e}")
            return None
    
    @classmethod
    def save_step(
        cls,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_id: str,
        step: str,
        step_number: int
    ) -> bool:
        """
        Save both DF values and mask for a processing step.
        
        Args:
            df_values: DF values array
            mask: Mask array
            window_id: Window identifier
            step: Step name
            step_number: Sequential step number
            
        Returns:
            True if both saved successfully, False otherwise
        """
        if not settings.SAVE_IMAGES:
            return True
            
        df_path = cls.save_df_values(df_values, window_id, step, step_number)
        mask_path = cls.save_mask(mask, window_id, step, step_number)
        
        success = df_path is not None and mask_path is not None
        if success:
            logger.info(f"Window '{window_id}' step '{step}': saved to {settings.IMAGES_OUTPUT_DIR}")
        return success
    
    @classmethod
    def save_context_state(
        cls,
        context: "WindowProcessingContext",
        window_id: str,
        step_number: int
    ) -> bool:
        """
        Save processing context state based on step number.
        
        Automatically determines which images to save and step name from step_number.
        
        Args:
            context: WindowProcessingContext with processing state
            window_id: Window identifier
            step_number: Step number in pipeline (1-5 corresponding to ProcessingStep enum order)
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not settings.SAVE_IMAGES:
            return True
        
        # Map step number to ProcessingStep enum
        steps = list(ProcessingStep)
        if step_number < 1 or step_number > len(steps):
            return False
        
        step_name = steps[step_number - 1].value
        
        # Determine which images are available at this step
        if step_number <= 2:  # Position and Standardize steps
            if context.original_images:
                return cls.save_step(
                    context.original_images.df_values,
                    context.original_images.mask,
                    window_id,
                    step_name,
                    step_number
                )
        elif step_number == 3:  # Rotate step
            if context.original_images:
                return cls.save_step(
                    context.original_images.df_values,
                    context.original_images.mask,
                    window_id,
                    step_name,
                    step_number
                )
        elif step_number == 4:  # Crop step
            if context.cropped:
                return cls.save_step(
                    context.cropped.images.df_values,
                    context.cropped.images.mask,
                    window_id,
                    step_name,
                    step_number
                )
        # Step 5 (translation) doesn't produce new images
        
        return True