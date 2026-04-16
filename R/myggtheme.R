library("ggplot2")
library("ggthemes")

theme_adl <- function() {
    return(
        theme_void() +
            theme(
                # Labels
                plot.title = element_text(
                    size = 16,
                    family = "mono",
                    face = "bold.italic",
                    color = "black",
                    hjust = 0.5,
                    margin = margin(b = 10, t = 10)
                ),
                plot.title.position = "plot",
                axis.title.x = element_text(
                    size = 12,
                    family = "mono",
                    face = "bold",
                    color = "black",
                    angle = 0,
                    margin = margin(t = 6)
                ),
                axis.title.y = element_text(
                    size = 12,
                    family = "mono",
                    face = "bold",
                    color = "black",
                    angle = 90,
                    margin = margin(r = 6)
                ),
                axis.text.y = element_text(
                    size = 10,
                    family = "mono",
                    color = "black",
                    margin = margin(r = 6)
                ),
                axis.text.x = element_text(
                    size = 10,
                    family = "mono",
                    color = "black",
                    margin = margin(t = 6)
                ),
                # Ticks and lines
                axis.ticks.length = unit(0.2, "cm"),
                axis.ticks = element_line(color = "black", linewidth = 0.7),
                axis.line.x = element_line(colour = "black", linewidth = 1),
                axis.line.y = element_line(colour = "black", linewidth = 1),
                axis.line = element_blank(),
                panel.grid.major = element_line(colour = "lightgrey", linewidth = 0.5),
                panel.grid.minor = element_line(colour = "lightgrey", linewidth = 0.3),
                # Legend
                legend.title = element_text(
                    size = 12,
                    family = "mono",
                    face = "bold",
                    color = "black",
                    margin = margin(r = 4, b = 2, t = 2, l = 4),
                    hjust = 0.5
                ),
                legend.text = element_text(
                    size = 10,
                    family = "mono",
                    color = "black",
                    margin = margin(r = 4, b = 2, t = 2, l = 4),
                    hjust = 0.5
                ),
                legend.background = element_rect(
                    fill = "ivory",
                    color = "black",
                    linewidth = 1
                ),
                legend.key = element_rect(colour = "black", fill = NA),
                legend.key.width = unit(0.75, "cm"),
                legend.key.height = unit(0.75, "cm"),
                legend.key.size = unit(0.6, "cm"),
                legend.position = "right",
                legend.text.align = 0.5,
                legend.title.align = 0.5,
                # Faceting
                strip.background = element_rect(
                    fill = "ivory",
                    color = "black",
                    linewidth = 1
                ),
                strip.text = element_text(
                    size = 12,
                    family = "mono",
                    face = "italic",
                    color = "black",
                    margin = margin(t = 4, b = 4) 
                ),
                panel.spacing = unit(0.5, "cm"),
                plot.margin = margin(t = 0.5, r = 0.5, b = 0.5, l = 0.5, unit = "cm"),
                plot.background = element_rect(fill = "white"),
                panel.background = element_rect(fill = "white")
            )
    )
}

continuous_palette_ocean_sunset <- c(
    "#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6", "#ee9b00", "#ca6702", "#bb3e03", "#ae2012", "#9b2226"
)
scale_continuous_colour_ocean_sunset <- function(...) {
    ggplot2::scale_colour_gradientn(
        colours = continuous_palette_ocean_sunset,
        ...
    )
}
scale_continuous_fill_ocean_sunset <- function(...) {
    ggplot2::scale_fill_gradientn(
        colours = continuous_palette_ocean_sunset,
        ...
    )
}
scale_discrete_colour_ocean_sunset <- function(n, ...) {
  colors <- grDevices::colorRampPalette(continuous_palette_ocean_sunset)(n)
  ggplot2::scale_color_manual(
    values = colors,
    ...
  )
}

scale_discrete_fill_ocean_sunset <- function(n, ...) {
  colors <- grDevices::colorRampPalette(continuous_palette_ocean_sunset)(n)
  ggplot2::scale_fill_manual(
    values = colors,
    ...
  )
}

continuous_palette_midnight_rose <- c(
    "#34091e", "#430c27", "#55062d", "#660033", "#802754", "#994d74", "#b37495", "#cc9ab5", "#ecc5dd", "#f3dbea"
)
scale_continuous_colour_midnight_rose <- function(...) {
    ggplot2::scale_colour_gradientn(
        colours = continuous_palette_midnight_rose,
        ...
    )
}
scale_continuous_fill_midnight_rose <- function(...) {
    ggplot2::scale_fill_gradientn(
        colours = continuous_palette_midnight_rose,
        ...
    )
}
scale_discrete_colour_midnight_rose <- function(n, ...) {
  colors <- grDevices::colorRampPalette(continuous_palette_midnight_rose)(n)
  ggplot2::scale_color_manual(
    values = colors,
    ...
  )
}

scale_discrete_fill_midnight_rose <- function(n, ...) {
  colors <- grDevices::colorRampPalette(continuous_palette_midnight_rose)(n)
  ggplot2::scale_fill_manual(
    values = colors,
    ...
  )
}

discrete_palette_colourful <- c(
    "#4d86a5", "#cf0bf1", "#75f2fb", "#133b91", "#98da1f", "#fc9f5b", "#d60b2d", "#c3c4e9", "#5d2689", "#378b64"
)
scale_discrete_colour_colourful <- function(...) {
    ggplot2::scale_colour_manual(
        values = discrete_palette_colourful,
        ...
    )
}
scale_discrete_fill_colourful <- function(...) {
    ggplot2::scale_fill_manual(
        values = discrete_palette_colourful,
        ...
    )
}

discrete_palette_dark_garden <- c(
    "#011936", "#465362", "#82a3a1", "#9fc490", "#c0dfa1"
)
scale_discrete_colour_dark_garden <- function(...) {
    ggplot2::scale_colour_manual(
        values = discrete_palette_dark_garden,
        ...
    )
}
scale_discrete_fill_dark_garden <- function(...) {
    ggplot2::scale_fill_manual(
        values = discrete_palette_dark_garden,
        ...
    )
}

# # Test 1: Simple scatter plot with clean axes
# ggplot(mtcars, aes(wt, mpg)) +
# geom_point(size = 3, color = "darkblue") +
# scale_x_continuous(expand = c(0.05, 0.05)) +
# scale_y_continuous(expand = c(0.05, 0.05)) +
# labs(
#     title = "Fuel Efficiency vs Weight",
#     x = "Weight (1000 lbs)",
#     y = "Miles Per Gallon"
# ) +
# theme_adl()

# # Test 2: Boxplot with faceting (shows facet styling)
# ggplot(mtcars, aes(factor(cyl), mpg, fill = factor(cyl))) +
# geom_boxplot() +
# facet_wrap(~am, labeller = labeller(am = c("0" = "Automatic", "1" = "Manual"))) +
# scale_x_discrete(expand = c(0.1, 0.1)) +
# scale_y_continuous(expand = c(0.05, 0.05)) +
# labs(
#     title = "MPG by Cylinders and Transmission",
#     x = "Number of Cylinders",
#     y = "Miles Per Gallon",
#     fill = "Cylinders"
# ) +
# scale_discrete_fill_dark_garden() +
# theme_adl()

# # Test 3: Line plot with legend
# iris_summary <- aggregate(Sepal.Length ~ Species, iris, mean)
# ggplot(iris, aes(Sepal.Width, Sepal.Length, color = Species)) +
# geom_point(size = 2) +
# geom_smooth(method = "lm", se = FALSE, linewidth = 1) +
# scale_x_continuous(expand = c(0.05, 0.05)) +
# scale_y_continuous(expand = c(0.05, 0.05)) +
# labs(
#     title = "Sepal Dimensions by Species",
#     x = "Sepal Width (cm)",
#     y = "Sepal Length (cm)",
#     color = "Species"
# ) +
#     scale_discrete_colour_dark_garden() +
#     theme_adl()
