import cv2
import numpy as np
from datetime import datetime

def process_prediction(results, image, output_path):
    # Get predictions data
    predictions = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            name = result.names[cls]
            
            predictions.append({
                'class': name,
                'confidence': round(conf, 2),
                'bbox': [x1, y1, x2, y2]
            })
    
    # Draw on image
    annotated_frame = results[0].plot()
    cv2.imwrite(output_path, annotated_frame)
    
    # Calculate stats
    total_damages = len(predictions)
    damage_types = list(set([p['class'] for p in predictions]))
    avg_confidence = round(np.mean([p['confidence'] for p in predictions]), 2) if predictions else 0
    
    stats = {
        'total_damages': total_damages,
        'damage_types': damage_types,
        'average_confidence': avg_confidence,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        'predictions': predictions,
        'stats': stats,
        'annotated_image': annotated_frame
    }