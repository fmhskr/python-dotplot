import math
from os import PathLike
from typing import Union, Sequence, Callable

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import gridspec
from matplotlib import pyplot as plt


class DotPlot(object):
    DEFAULT_ITEM_HEIGHT = 0.3
    DEFAULT_ITEM_WIDTH = 0.35
    DEFAULT_LEGENDS_WIDTH = .5
    MIN_FIGURE_HEIGHT = 3

    def __init__(self, df_size: pd.DataFrame,
                 df_color: Union[pd.DataFrame, None] = None,
                 ):
        """
        Construction a `DotPlot` object from `df_size` and `df_color`

        :param df_size: the DataFrame object represents the scatter size in dotplot
        :param df_color: the DataFrame object represents the color in dotplot
        """
        __slots__ = ['size_data', 'color_data', 'height_item', 'width_item', 'resized_size_data']
        if (df_color is not None) & (df_size.shape != df_color.shape):
            raise ValueError('df_size and df_color should have the same dimension')
        self.size_data = df_size
        self.color_data = df_color
        self.height_item, self.width_item = df_size.shape
        self.resized_size_data: pd.DataFrame

    def __get_figure(self):
        _text_max = math.ceil(self.size_data.index.map(len).max() / 15)
        mainplot_height = self.height_item * self.DEFAULT_ITEM_HEIGHT
        mainplot_width = (
                (_text_max + self.width_item) * self.DEFAULT_ITEM_WIDTH
        )
        figure_height = max([self.MIN_FIGURE_HEIGHT, mainplot_height])
        figure_width = mainplot_width + self.DEFAULT_LEGENDS_WIDTH
        plt.style.use('seaborn-white')
        fig = plt.figure(figsize=(figure_width, figure_height))
        gs = gridspec.GridSpec(nrows=2, ncols=2, wspace=0.15, hspace=0.15,
                               width_ratios=[mainplot_width, self.DEFAULT_LEGENDS_WIDTH])
        ax = fig.add_subplot(gs[:, 0])
        ax_cbar = fig.add_subplot(gs[1, 1])
        ax_legend = fig.add_subplot(gs[0, 1])
        return ax, ax_cbar, ax_legend, fig

    @classmethod
    def parse_from_tidy_data(cls, data_frame: pd.DataFrame, item_key: str, group_key: str, sizes_key: str,
                             color_key: str, selected_item: Union[None, Sequence] = None,
                             selected_group: Union[None, Sequence] = None, *,
                             sizes_func: Union[None, Callable] = None, color_func: Union[None, Callable] = None
                             ):
        """

        class method for conveniently constructing DotPlot from tidy data

        :param data_frame:
        :param item_key:
        :param group_key:
        :param sizes_key:
        :param color_key:
        :param selected_item: default None, if specified, this should be subsets of `item_key` in `data_frame`
                              alternatively, this param can be used as self-defined item order definition.
        :param selected_group: Same as `selected_item`, for group order and subset groups
        :param sizes_func:
        :param color_func:
        :return:
        """
        data_frame = data_frame[[item_key, group_key, sizes_key, color_key]]
        _original_item_order = data_frame[item_key].tolist()
        _original_item_order = _original_item_order[::-1]
        if sizes_func is not None:
            data_frame[sizes_key] = data_frame[sizes_key].map(sizes_func)
        if color_func is not None:
            data_frame[color_key] = data_frame[color_key].map(color_func)
        data_frame = data_frame.pivot(index=item_key, columns=group_key, values=[color_key, sizes_key])
        data_frame = data_frame.loc[_original_item_order, :]
        if selected_item is not None:
            data_frame = data_frame.loc[selected_item, :]
        if selected_group is not None:
            data_frame = data_frame.loc[:, selected_group]

        data_frame.columns = data_frame.columns.map(lambda x: '_'.join(x))
        data_frame = data_frame.fillna(0)
        color_df = data_frame.loc[:, data_frame.columns.str.startswith(color_key)]
        sizes_df = data_frame.loc[:, data_frame.columns.str.startswith(sizes_key)]
        color_df.columns = color_df.columns.map(lambda x: '_'.join(x.split('_')[1:]))
        sizes_df.columns = sizes_df.columns.map(lambda x: '_'.join(x.split('_')[1:]))
        return cls(color_df, sizes_df)

    def __get_coordinates(self, size_factor):
        X = list(range(1, self.width_item + 1)) * self.height_item
        Y = sorted(list(range(1, self.height_item + 1)) * self.width_item)
        self.resized_size_data = self.size_data.applymap(func=lambda x: x * size_factor)
        return X, Y

    def __draw_dotplot(self, ax, size_factor, cmap, vmin, vmax):
        X, Y = self.__get_coordinates(size_factor)
        if self.color_data is None:
            sct = ax.scatter(X, Y, c='r', cmap=cmap, s=self.resized_size_data.values.flatten(),
                             edgecolors='none', linewidths=0, vmin=vmin, vmax=vmax)
        else:
            sct = ax.scatter(X, Y, c=self.color_data.values.flatten(), s=self.resized_size_data.values.flatten(),
                             edgecolors='none', linewidths=0, vmin=vmin, vmax=vmax, cmap=cmap)
        width, height = self.width_item, self.height_item
        ax.set_xlim([0.5, width + 0.5])
        ax.set_ylim([0.6, height + 0.6])
        ax.set_xticks(range(1, width + 1))
        ax.set_yticks(range(1, height + 1))
        ax.set_xticklabels(self.size_data.columns.tolist(), rotation='vertical')
        ax.set_yticklabels(self.size_data.index.tolist())
        ax.tick_params(axis='y', length=5, labelsize=15, direction='out')
        ax.tick_params(axis='x', length=5, labelsize=15, direction='out')
        return sct

    @staticmethod
    def __draw_color_bar(ax, sct: mpl.collections.PathCollection, cmap, vmin, vmax):
        gradient = np.linspace(1, 0, 500)
        gradient = gradient[:, np.newaxis]
        im = ax.imshow(gradient, aspect='auto', cmap=cmap, origin='upper', extent=[.2, 0.3, 0.5, -0.5])
        ax.set_xticks([])
        ax.set_yticks([])
        ax_cbar2 = ax.twinx()
        _ = ax_cbar2.set_yticks([0, 1000])
        if vmax is None:
            vmax = math.ceil(sct.get_array().max())
        if vmin is None:
            vmin = math.floor(sct.get_array().min())
        _ = ax_cbar2.set_yticklabels([vmin, vmax])
        _ = ax_cbar2.set_ylabel('-log10(pvalue)')

    @staticmethod
    def __draw_legend(ax, sct: mpl.collections.PathCollection, size_factor):
        handles, labels = sct.legend_elements(prop="sizes", alpha=1,
                                              func=lambda x: x / size_factor,
                                              color='#58000C')
        if len(handles) > 3:
            handles = np.asarray(handles)
            labels = np.asarray(labels)
            handles = handles[[0, math.ceil(len(handles) / 2), -1]]
            labels = labels[[0, math.ceil(len(labels) / 2), -1]]
        _ = ax.legend(handles, labels, title="Sizes", loc='center left')  # bbox_to_anchor=(0.9, 0., 0.4, 0.4)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def plot(self, size_factor: float = 15,
             vmin: float = 0, vmax: float = None,
             path: Union[PathLike, None] = None,
             cmap: Union[str, mpl.colors.Colormap] = 'Reds'):
        """

        :param size_factor: `size factor` * `value` for the actually representation of scatter size in the final figure
        :param vmin: `vmin` in `matplotlib.pyplot.scatter`
        :param vmax: `vmax` in `matplotlib.pyplot.scatter`
        :param path: path to save the figure
        :param cmap: color map supported by matplotlib
        :return:
        """
        ax, ax_cbar, ax_legend, fig = self.__get_figure()
        scatter = self.__draw_dotplot(ax, size_factor, cmap, vmin, vmax)
        self.__draw_legend(ax_legend, scatter, size_factor)
        self.__draw_color_bar(ax_cbar, scatter, cmap, vmin, vmax)
        if path:
            fig.savefig(path, dpi=300, bbox_inches='tight')  #
        return scatter

    def __str__(self):
        return 'DotPlot object with data point in shape %s' % str(self.size_data.shape)

    __repr__ = __str__
