import os
import base64

from unstructured.documents.elements import Element

def separate_content_types(chunk, image_dir: str, image_counter: dict) -> dict[str, any]:
    """
    Analyze chunk content and extract text, tables, and images.
    Uses mutable dict to track image counter across calls.
    """
    content_data = {
        'text': chunk.text,
        'tables': [],
        'image_base64': [],
        'images_dirpath': [],  # now will hold folder + filename
        'page_no': [],
        'types': ['text']
    }

    for element in chunk.metadata.orig_elements:
        element_type = type(element).__name__

        # Handle page numbers
        if 'metadata' in element.to_dict():
            page_no = element.to_dict()['metadata'].get('page_number')
            if page_no and page_no not in content_data['page_no']:
                content_data['page_no'].append(page_no)

        # Handle tables
        if element_type == 'Table':
            if 'table' not in content_data['types']:
                content_data['types'].append('table')
            table_html = getattr(element.metadata, 'text_as_html', element.text)
            content_data['tables'].append(table_html)

        # Handle images
        elif element_type == 'Image':
            if hasattr(element.metadata, 'image_base64'):
                if 'image' not in content_data['types']:
                    content_data['types'].append('image')

                image_base64 = element.metadata.image_base64

                try:
                    # Generate filename and path
                    image_filename = f"image_{image_counter['count']:04d}.png"
                    image_path = os.path.join(image_dir, image_filename)

                    # Decode and save image
                    with open(image_path, "wb") as img_file:
                        img_file.write(base64.b64decode(image_base64))

                    # ✅ Store relative folder + filename (e.g. "Images/image_0001.png")
                    folder_name = os.path.basename(image_dir.rstrip(os.sep))
                    relative_path = os.path.join(folder_name, image_filename).replace("\\", "/")
                    content_data['images_dirpath'].append(relative_path)

                    # Keep base64 for AI processing
                    content_data['image_base64'].append(image_base64)

                    print(f"      Saved: {relative_path}")
                    image_counter['count'] += 1

                except Exception as e:
                    print(f"      Failed to save image {image_counter['count']}: {e}")

    return content_data
