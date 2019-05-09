import React, { Component } from 'react';
import {Line} from 'react-chartjs-2';

function PortfolioChart(props) {
    const {portfolios, labels} = props;
    const colours = {
        'BITTREX': {
            backgroundColor: 'rgba(167, 232, 192,.1)',
            borderColor: 'rgba(167, 232, 192,.55)'
        },
        'BINANCE': {
            backgroundColor: 'rgba(237, 220, 220,.1)',
            borderColor: 'rgba(237, 220, 220,.55)'
        }
    }
    return <Line height={50}
                 data={{
                         labels: labels,
                         type: 'line',
                         datasets: Object.keys(portfolios).map(exchange => {
                             return {
                                 data: portfolios[exchange].map(function (d) {
                                     return parseFloat(d);
                                 }),
                                 label: exchange,
                                 backgroundColor: colours[exchange].backgroundColor,
                                 borderColor: colours[exchange].borderColor,
                             }
                         }
                         )

                 }
}
            options={
                {
                    maintainAspectRatio: true,
                    legend: {
                    display: false
                },
                    layout: {
                    padding: {
                        left: 0,
                        right: 0,
                        top: 0,
                        bottom: 0
                    }
                },
                    responsive: true,
                    scales: {
                    xAxes: [{
                        gridLines: {
                            color: 'transparent',
                            zeroLineColor: 'transparent'
                        },
                        ticks: {
                            fontSize: 2,
                            fontColor: 'transparent'
                        }
                    }],
                    yAxes: [{
                        display: false,
                        ticks: {
                            display: false,
                        }
                    }]
                },
                    title: {
                    display: false,
                },
                    elements: {
                    line: {
                        borderWidth: 0
                    },
                    point: {
                        radius: 0,
                        hitRadius: 10,
                        hoverRadius: 4
                    }
                }
                }
            }
    />
}

export {PortfolioChart}