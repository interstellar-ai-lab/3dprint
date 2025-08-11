from PIL import Image
import matplotlib.pyplot as plt
import os

def crop_multiview_image(image: Image.Image) -> dict:
    """Crop multiview image into 4 separate views in the order [front, left, back, right]"""
    width, height = image.size
    half_width = width // 2
    half_height = height // 2
    
    # Crop into 4 quadrants
    # Top left: front view
    front_view = image.crop((0, 0, half_width, half_height))
    # Top right: left view  
    left_view = image.crop((half_width, 0, width, half_height))
    # Bottom left: back view
    back_view = image.crop((0, half_height, half_width, height))
    # Bottom right: right view
    right_view = image.crop((half_width, half_height, width, height))
    
    return {
        "front": front_view,
        "left": left_view, 
        "back": back_view,
        "right": right_view
    }

def display_cropped_views(image_path: str):
    """Load image, crop it, and display all views"""
    # Load the image
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return
    
    print(f"Loading image from: {image_path}")
    image = Image.open(image_path)
    print(f"Original image size: {image.size}")
    
    # Crop the image
    cropped_views = crop_multiview_image(image)
    
    # Create a figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Multiview Image Cropping Results (API Order: front, left, back, right)', fontsize=16)
    
    # Display original image
    axes[0, 0].imshow(image)
    axes[0, 0].set_title('Original Image')
    axes[0, 0].axis('off')
    
    # Display cropped views in API order
    views = [
        ('front', 0, 1),
        ('left', 0, 2), 
        ('back', 1, 0),
        ('right', 1, 1)
    ]
    
    for view_name, row, col in views:
        view_image = cropped_views[view_name]
        axes[row, col].imshow(view_image)
        axes[row, col].set_title(f'{view_name.title()} View ({view_image.size[0]}x{view_image.size[1]})')
        axes[row, col].axis('off')
    
    # Hide the last subplot
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Save individual views
    output_dir = "cropped_views"
    os.makedirs(output_dir, exist_ok=True)
    
    for view_name, view_image in cropped_views.items():
        output_path = os.path.join(output_dir, f"{view_name}_view.png")
        view_image.save(output_path)
        print(f"Saved {view_name} view to: {output_path}")
    
    print(f"\nAll cropped views saved to '{output_dir}' directory")
    
    # Print the order for API usage
    print("\nAPI Order: [front, left, back, right]")
    for view_name in ["front", "left", "back", "right"]:
        view_image = cropped_views[view_name]
        print(f"  {view_name}: {view_image.size[0]}x{view_image.size[1]}")

if __name__ == "__main__":
    # Test with the computer.png image
    image_path = "/Users/Interstellar/Downloads/computer.png"
    display_cropped_views(image_path)
