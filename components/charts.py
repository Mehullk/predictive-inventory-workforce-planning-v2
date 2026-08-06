import plotly.graph_objects as go


def apply_theme(fig):

    fig.update_layout(

        template="plotly_white",

        paper_bgcolor="white",
        plot_bgcolor="white",

        font=dict(
            family="Inter",
            color="#24324A",
            size=14,
        ),

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),

        title_font=dict(
            size=22,
            color="#24324A",
        ),

        legend=dict(
            orientation="h",
            y=1.08,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                size=13,
                color="#5C6E88",
            ),
        ),

        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#BFD8FF",
            font_size=13,
            font_family="Inter",
            font_color="#24324A",
        ),

        hovermode="x unified",

    )

    fig.update_xaxes(

        showgrid=False,

        showline=False,

        zeroline=False,

        tickfont=dict(
            color="#75839D",
        ),

    )

    fig.update_yaxes(

        showgrid=True,

        gridcolor="#E4ECF8",

        gridwidth=1,

        zeroline=False,

        showline=False,

        tickfont=dict(
            color="#75839D",
        ),

    )

    return fig


def forecast_chart(df):

    fig = go.Figure()

    forecast_col = "Forecast"

    if "PredictedUnitsSold" in df.columns:
        forecast_col = "PredictedUnitsSold"

    if "Upper95CI" in df.columns:

        fig.add_trace(

            go.Scatter(

                x=df["Date"],
                y=df["Upper95CI"],

                mode="lines",

                line=dict(width=0),

                showlegend=False,

                hoverinfo="skip",

            )

        )

    if "Lower95CI" in df.columns:

        fig.add_trace(

            go.Scatter(

                x=df["Date"],
                y=df["Lower95CI"],

                mode="lines",

                fill="tonexty",

                fillcolor="rgba(236,72,153,.35)",

                line=dict(width=0),

                name="95% Confidence",

            )

        )

    fig.add_trace(

        go.Scatter(

            x=df["Date"],
            y=df[forecast_col],

            mode="lines",

            name="Forecast",

            line=dict(
                color="#EC4899",

                width=4,

                shape="spline",

                smoothing=0.6,

            ),

        )

    )

    fig.update_layout(

        title="90-Day Sales Forecast",

    )

    return apply_theme(fig)


def inventory_chart(df):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=df["Date"],
            y=df["ClosingStock"],

            mode="lines",

            name="Closing Stock",

            line=dict(

                color="#EC4899",

                width=4,

                shape="spline",

                smoothing=0.5,

            ),

        )

    )

    if "ReorderPoint" in df.columns:

        fig.add_trace(

            go.Scatter(

                x=df["Date"],
                y=df["ReorderPoint"],

                mode="lines",

                name="Reorder Point",

                line=dict(

                    color="#C084FC",

                    width=3,

                    dash="dash",

                ),

            )

        )

    if "SafetyStock" in df.columns:

        fig.add_trace(

            go.Scatter(

                x=df["Date"],
                y=df["SafetyStock"],

                mode="lines",

                name="Safety Stock",

                line=dict(

                    color="#FFD166",

                    width=3,

                    dash="dot",

                ),

            )

        )

    fig.update_layout(

        title="Inventory Levels",

    )

    return apply_theme(fig)


def workforce_chart(df):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=df["Date"],
            y=df["RequiredWorkers"],

            name="Required Workers",

            marker_color="#F9A8D4",

        )

    )

    fig.add_trace(

        go.Scatter(

            x=df["Date"],
            y=df["CurrentStaff"],

            mode="lines",

            name="Current Staff",

            line=dict(

                color="#A855F7",

                width=4,

                shape="spline",

                smoothing=0.6,

            ),

        )

    )

    fig.update_layout(

        title="Workforce Requirement",

        barmode="group",

    )

    return apply_theme(fig)