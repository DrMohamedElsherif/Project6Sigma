import matplotlib.pyplot as plt
import os


def add_header_or_footer_to_a4_portrait(fig, image_path, position='header', page_number=None, total_pages=None):
    """
    Add header or footer image to an A4 portrait matplotlib figure.
    
    Parameters:
        fig: matplotlib figure object
        image_path: path to the image file
        position: 'header' or 'footer' indicating where to place the image
        page_number: Optional - current page number to display
        total_pages: Optional - total number of pages to display
    
    Returns:
        axes object containing the image
    """
    # Check if image file exists
    if not os.path.isfile(image_path):
        # Create an empty axes for positioning
        if position == 'header':
            ax = fig.add_axes([0, 0.95, 1, 0.05])
        else:
            ax = fig.add_axes([0, 0, 1, 0.05])
        ax.axis('off')
        
        # Add page number if provided
        if page_number is not None:
            page_text = f"Page {page_number}"
            if total_pages is not None:
                page_text += f" of {total_pages}"
            
            if position == 'footer':
                ax.text(0.5, 0.5, page_text, ha='center', va='center', fontsize=9)
        
        return ax
    
    # Load the image and get its dimensions
    img = plt.imread(image_path)
    img_h, img_w = img.shape[:2]
    
    # Calculate height in inches based on figure width (scale image to fit width)
    fig_width_in = fig.get_figwidth()
    height_in = fig_width_in * (img_h / img_w) # Adjusted to 80% height
    rel_height = height_in / fig.get_figheight()
    
    # Create an Axes in figure coordinates
    if position == 'header':
        # Header at the top
        ax = fig.add_axes([0, 1 - rel_height, 1, rel_height])
    else:
        # Footer at the bottom
        ax = fig.add_axes([0, 0, 1, rel_height])
    
    ax.axis('off')
    ax.imshow(img, aspect='equal')
    
    # Add page number if provided
    if page_number is not None:
        page_text = f"{page_number}"
        if total_pages is not None:
            page_text += f" / {total_pages}"
        
        if position == 'footer':
            # Position the text at the bottom right of the footer
            ax.text(0.93, 0.7, page_text, ha='right', va='bottom', 
                   fontsize=9, transform=ax.transAxes)
    
    return ax