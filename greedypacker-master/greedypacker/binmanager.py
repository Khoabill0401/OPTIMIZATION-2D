#!/usr/bin/env python
"""
BinManager

The main program interface for the package. BinPack manages
creation and ranking of bins and returns layout dictionaries
for packed bins.

"""
from typing import List, Union, Callable, Optional, Any
from . import item
from . import shelf
from . import guillotine
from . import maximal_rectangles
from . import skyline

# Type Aliases:
Algorithm = Union[shelf.Sheet, guillotine.Guillotine, maximal_rectangles.MaximalRectangle]


class BinManager:
    """
    Interface Class.
    """
    def __init__(self, bin_width: int = 8,
                 bin_height: int = 4,
                 bin_algo: str = 'bin_best_fit',
                 pack_algo: str = 'guillotine',
                 heuristic: str ='default',
                 split_heuristic: str = 'default',
                 rotation: bool = True,
                 rectangle_merge: bool = True,
                 wastemap: bool = True,
                 sorting: bool = True,
                 sorting_heuristic: str = 'DESCA') -> None:
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.items = [] # type: List[item.Item]
        self.bin_count = 0
        self.bin_algo = bin_algo
        self.pack_algo = pack_algo
        self.heuristic = heuristic

        if bin_algo == 'bin_best_fit':
            self.bin_sel_algo = self._bin_best_fit
        elif bin_algo == 'bin_first_fit':
            self.bin_sel_algo =  self._bin_first_fit
        self.heuristic = heuristic
        self.algorithm = pack_algo

        self.split_heuristic = split_heuristic
        self.sorting = sorting
        self.sorting_heuristic = sorting_heuristic
        self.rotation = rotation
        self.rectangle_merge = rectangle_merge
        self.wastemap = wastemap

        defaultBin = self._bin_factory() 
        self.bins = [defaultBin]

    def items_sort(self): 
        # By Area Ascending
        if self.sorting_heuristic == 'ASCA':
            key = lambda el: el.width*el.height
            self.items.sort(key=key, reverse=False)
        # By Area Descending
        elif self.sorting_heuristic == 'DESCA':
            key = lambda el: el.width*el.height
            self.items.sort(key=key, reverse=True)
        # By Shorter Side Ascending
        elif self.sorting_heuristic == 'ASCSS':
            key = lambda el: el.width if el.width < el.height else el.height
            self.items.sort(key=key, reverse=False)
        # By Shorter Side Descending
        elif self.sorting_heuristic == 'DESCSS':
            key = lambda el: el.width if el.width < el.height else el.height
            self.items.sort(key=key, reverse=True)
        # By Longer Side Ascending
        elif self.sorting_heuristic == 'ASCLS':
            key = lambda el: el.width if el.width > el.height else el.height
            self.items.sort(key=key, reverse=False)
        # By Longer Side Descending
        elif self.sorting_heuristic == 'DESCLS':
            key = lambda el: el.width if el.width > el.height else el.height
            self.items.sort(key=key, reverse=True)
        # By Perimiter Ascending
        elif self.sorting_heuristic == 'ASCPERIM':
            key = lambda el: (2*el.width)+(2*el.height)
            self.items.sort(key=key, reverse=False)
        # By Perimiter Descending
        elif self.sorting_heuristic == 'DESCPERIM':
            key = lambda el: (2*el.width)+(2*el.height)
            self.items.sort(key=key, reverse=True)
        # By Difference in Side Length Ascending
        elif self.sorting_heuristic == 'ASCDIFF':
            key = lambda el: abs(el.width-el.height)
            self.items.sort(key=key, reverse=False)
        # By Difference in Side Length Descending
        elif self.sorting_heuristic == 'DESCDIFF':
            key = lambda el: abs(el.width-el.height)
            self.items.sort(key=key, reverse=True)
        # By Side Ratio Ascending
        elif self.sorting_heuristic == 'ASCRATIO':
            key = lambda el: el.width/el.height
            self.items.sort(key=key, reverse=False)
        # By Side Ratio Descending
        elif self.sorting_heuristic == 'DESCRATIO':
            key = lambda el: el.width/el.height
            self.items.sort(key=key, reverse=True)
        # Default to DESCA
        else:
            key = lambda el: el.width*el.height
            self.items.sort(key=key, reverse=True)

    def add_items(self, *items: item.Item) -> None:
        for item in items:
            self.items.append(item)
        if self.sorting:
            self.items_sort()


    def _bin_factory(self) -> Any:
        """
        Returns a bin with the specificed algorithm,
        heuristic, and dimensions
        """
        if self.algorithm == 'guillotine':
            return guillotine.Guillotine(self.bin_width, self.bin_height, self.rotation, self.heuristic,
                                         self.rectangle_merge, self.split_heuristic)
        elif self.algorithm == 'shelf':
            return shelf.Sheet(self.bin_width, self.bin_height, self.rotation, self.wastemap, self.heuristic)

        elif self.algorithm == 'maximal_rectangle':
            return maximal_rectangles.MaximalRectangle(self.bin_width, self.bin_height, self.rotation, self.heuristic)

        elif self.algorithm == 'skyline':
            return skyline.Skyline(self.bin_width, self.bin_height, self.rotation, self.wastemap, self.heuristic)
        raise ValueError('Error: No such Algorithm')


    def _bin_first_fit(self, item: item.Item) -> None:
        """
        Insert into the first bin that fits the item
        """
        result = False
        for binn in self.bins:
            result = binn.insert(item, self.heuristic)
            if result:
                break
        if not result:
            self.bins.append(self._bin_factory())
            self.bins[-1].insert(item, self.heuristic)


    def _bin_best_fit(self, item: item.Item) -> bool:
        """
        Insert into the bin that best fits the item
        """

        # Ensure item can theoretically fit the bin
        item_fits = False
        if (item.width <= self.bin_width and 
            item.height <= self.bin_height):
            item_fits = True
        if (self.rotation and 
            (item.height <= self.bin_width and 
            item.width <= self.bin_height)):
            item_fits = True
        if not item_fits:
            raise ValueError("Error! item too big for bin")

        scores = []
        for binn in self.bins:
            s, _, _ = binn._find_best_score(item)[:3]
            if s is not None:
                scores.append((s, binn))
        if scores:
            _, best_bin = min(scores, key=lambda x: x[0])
            return best_bin.insert(item)

        new_bin = self._bin_factory()
        new_bin.insert(item, self.heuristic)
        self.bins.append(new_bin)
        return True


    def execute(self) -> None:
        """
        Loop over all items and attempt insertion
        """
        for item in self.items:
            self.bin_sel_algo(item)
