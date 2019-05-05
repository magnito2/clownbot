import React, { Component } from 'react';
import {Line} from 'react-chartjs-2';

function PortfolioChart(props) {
    const {data} = props;
    return <Line height={50}
                 data={{
                         labels: data.map(function(d) {
                             return d.timestamp;
                         }),
                         type: 'line',
                         datasets: [{
                             data: data.map(function (d) {
                                 return parseFloat(d.btc_value);
                             }),
                             label: 'BTC_Value',
                             backgroundColor: 'rgba(255,255,255,.1)',
                             borderColor: 'rgba(255,255,255,.55)',
                         }
                         ]
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