def rectangles_overlap(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2)

def is_within_bounds(x, y, w, h, room_w, room_h):
    return 0 <= x <= room_w - w and 0 <= y <= room_h - h
