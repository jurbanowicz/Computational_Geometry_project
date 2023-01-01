from sortedcontainers import SortedSet

class Solution:
    def __init__(self, points) -> None:
        self.points = points

        self.p_events = SortedSet(key = lambda x : x.y)
        self.c_events = SortedSet(key = lambda x: x.y)
        self.arc = None

        self.result = []
        self.scenes = []

        bounds = bounding_box(points)

        self.low_left = bounds[0]
        self.up_right = bounds[1]

        for point in points:
            p = Point(point[0], point[1])
            self.p_events.add(p)

        
    def create_diagram(self):
        while self.p_events:
            
            if self.c_events and self.c_events[len(self.c_events) - 1].y >= self.p_events[len(self.p_events) - 1].y:
                self.handle_circle_event()

            else:
                self.handle_site_event()


        # handle the remaining circle events
        while self.c_events:
            self.handle_circle_event()


        self.finish_lines() # fisnish any uncompleted lines up to the bounding box

        fin = Point(self.low_left[0], self.low_left[1])
        self.add_scene(fin)
                


    def handle_site_event(self):
        point = self.p_events.pop()

        self.add_scene(point)

        self.arc_insert(point)

    def handle_circle_event(self):
        event = self.c_events.pop()

        self.add_scene(event)

        if event.valid:
            s = Line(event.p)
            self.result.append(s)

            a = event.a
            if a.prev is not None:
                a.prev.next = a.next
                a.prev.s1 = s
            if a.next is not None:
                a.next.prev = a.prev
                a.next.s0 = s

            if a.s0 is not None:
                a.s0.complete(event.p)
            if a.s1 is not None:
                a.s1.complete(event.p)

            if a.prev is not None: 
                self.check_circle_event(a.prev, event.y)
            if a.next is not None:
                self.check_circle_event(a.next, event.y)

    def check_circle_event(self, i, y0):
        if i.e is not None and i.e.y != self.up_right[1]:
            i.e.valid = False
        i.e = None

        if i.prev is None or i.next is None:
            return
        
        flag, y, o = self.circle(i.prev.p, i.p, i.next.p)
        if flag and y < self.up_right[1]:
            i.e = Event(y, o, i)
            self.c_events.add(i.e)

    def circle(self, a, b, c):
        # TODO check the if the value 1 is correct
        orientation = orient(a, b, c)
        if orientation >= 0:
            return False, None, None

        A = b.x - a.x
        B = b.y - a.y
        C = c.x - a.x
        D = c.y - a.y
        E = A*(a.x + b.x) + B*(a.y + b.y)
        F = C*(a.x + c.x) + D*(a.y + c.y)
        G = 2*(A*(c.y - b.y) - B*(c.x - b.x))

        ox = 1.0 * (D*E - B*F) / G
        oy = 1.0 * (A*F - C*E) / G

        y = oy - np.sqrt((a.x-ox)**2 + (a.y-oy)**2)
        o = Point(ox, oy)

        return True, y, o

    def arc_insert(self, point):
        if self.arc is None:
            self.arc = Arc(point)

        else:
            # find arcs directly above current event
            i = self.arc

            while i is not None:
                flag, z = self.intersect(point, i)

                if flag:
                    flag, z_2 = self.intersect(point, i.next)

                    if i.next is not None and not flag:
                        i.next.prev = Arc(i.p, i, i.next)
                        i.next = i.next.prev
                    else:
                        i.next = Arc(i.p, i)
                    i.next.s1 = i.s1

                    i.next.prev = Arc(point, i, i.next)
                    i.next = i.next.prev
                    i = i.next

                    seg = Line(z)
                    self.result.append(seg)
                    i.next.s1 = i.s0 = seg

                    seg = Line(z)
                    self.result.append(seg)
                    i.next.s0 = i.s1 = seg

                    self.check_circle_event(i, point.y)
                    self.check_circle_event(i.prev, point.y)
                    self.check_circle_event(i.next, point.y)

                    return

                i = i.next
            
            i = self.arc
            while i.next is not None:
                i = i.next
            i.next = Arc(point, i)

            # # TODO might have to fix x and y's 
            # x = self.low_left[0] # <- here we know the y not the x
            y = self.up_right[1]
            x = (i.next.p.x + i.p.x) / 2.0
            start = Point(x, y)

            seg = Line(start)
            i.s1 = i.next.s0 = seg
            self.result.append(seg)

                    

    def intersect(self, point, i):
        if i is None:
            return False, None
        if i.p.y == point.y:
            return False, None

        a = 0.0
        b = 0.0

        if i.prev is not None:
            a = (self.find_intersection(i.prev.p, i.p, 1.0*point.y)).x

        if i.next is not None:
            b = (self.find_intersection(i.p, i.next.p, 1.0*point.y)).x

        if i.prev is None or a <= point.x and i.next is None or point.x <= b:

            # TODO we know the px ad need to figure out py 
            # py = point.y
            # px = 1.0 * (i.p.x**2 + i.p.y**2 - point.x**2) / (2*i.p.x - 2*point.x)
            px = point.x
            py = 1.0 * (i.p.x**2 + i.p.y**2 - point.y**2) / (2*i.p.y - 2*point.y)
            res = Point(px, py)
            return True, res
        return False, None

    def find_intersection(self, p0, p1, l):
        p = p0
        if (p0.y == p1.y):
            px = (p0.x + p1.x) / 2.0
        elif p1.y == l:
            px = p1.x
        elif p0.y == l:
            px = p0.x
            p = p1
        
        else:
            z0 = 2.0 * (p0.y - l)
            z1 = 2.0 * (p1.y - l)

            a = 1.0/z0 - 1.0/z1
            b = -2.0 * (p0.x/z0 - p1.x/z1)
            c = 1.0 * (p0.x**2 + p0.y**2 - l**2) / z0 - 1.0 * (p1.x**2 + p1.y**2 - l**2) / z1

            px = 1.0 * (-b - np.sqrt(b*b - 4*a*c))/ (2*a)

        py = 1.0 * (p.y**2 + (p.x-px)**2 - l**2) / (2*p.y - 2*l)
        res = Point(px, py)
        return res

    def finish_lines(self):
        l = self.low_left[1] + (self.low_left[1] - self.up_right[1]) + (self.up_right[0] - self.low_left[0])
        i = self.arc

        while i.next is not None:
            if i.s1 is not None:
                p = self.find_intersection(i.p, i.next.p, l)
                i.s1.complete(p)
            i = i.next


    def add_scene(self, event):
        new_lines, new_points = self.find_current_output()
        current = Scene(points=[PointsCollection(self.points), PointsCollection(new_points, color = "red")],
        lines=[LinesCollection(new_lines), LinesCollection(lines = [((self.low_left[0], event.y), (self.up_right[0], event.y))], color = "red")])
        self.scenes.append(current)

    def find_current_output(self):
        p = []
        l = []
        for seg in self.result:
            if seg.done:
                a = seg.start.x, seg.start.y
                b = seg.end.x, seg.end.y
                l.append((a, b))
            else:
                p.append((seg.start.x, seg.start.y))

        return l, p



        
