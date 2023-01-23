import * as fos from '@fiftyone/state'
import * as foa from '/home/musausr/fiftyone/fiftyone/app/packages/aggregations'
import { useRecoilState, useRecoilValue as useVal, useResetRecoilState } from 'recoil'
import { useEffect, useState } from 'react'
import React from 'react'
import { useRef } from 'react';
import styled from "styled-components";
import { scrollbarStyles } from  "/home/musausr/fiftyone/fiftyone/app/packages/core/src/components/utils"
import Select from 'react-select';
import zoomPlugin from 'chartjs-plugin-zoom';
import { FaRedo } from 'react-icons/fa'
import { getFetchFunction } from  "/home/musausr/fiftyone/fiftyone/app/packages/utilities"

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

import { Line, getElementAtEvent } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
);

const Container = styled.div`
  ${scrollbarStyles}
  overflow-y: hidden;
  overflow-x: scroll;
  width: 100%;
  height: 100%;
  padding-left: 1rem;
`;

const LineContainer = styled.div`
  overflow-y: scroll;
  overflow-x: hidden;
  width: 100%;
  height: calc(100% - 4.5rem);
  ${scrollbarStyles}
`;

const ButtonRefresh = styled.button`
  border-width: 0px;
  height: 1.5rem;
  line-height: 1.5rem;
  margin: 0.25rem 5px 0.25rem 0px;
  cursor: pointer;
  display: inline-block;
  padding: 0px 1em;
  color: rgb(255, 255, 255);
  background-color: rgb(58, 61, 64);
  text-decoration: none;
  border-radius: 2px;
  font-weight: bold;
`;

const ButtonZoom = styled(ButtonRefresh)`
  float: right;
`;

const Chart: React.FC<{}> = () => { 
  
  const chartRef = useRef();
  
  const [selection, setSelection] = useRecoilState(fos.extendedSelection);
  //const expandSample = fos.useExpandSample();

  //const [ref, { height }] = useMeasure();
  
  const labels = getSpecificField({field:'id'})

  const dataStart = {
    labels,
    datasets: [
      {
        label: '',
        data: [],
      }
    ],
  };

  let options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Comparison chart',
      },
      zoom: {
        pan: {
          enabled: true,
          mode:'xy'
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true
          },
          mode: 'y',
        }
      }
    } 
  };

  const allFields = getFieldsName();
  const optionsSelect = [];
  const allData = {}
  const allColors = [];
  var path;
  var modal = false;
  var color;

  let i = 0;

  for (i = 0; i < allFields.length; i++) {
    optionsSelect.push({value: allFields[i], label: allFields[i]})
    allData[allFields[i]] = getSpecificField({field: allFields[i]})
    path = allFields[i];
    color = useVal(fos.pathColor({path, modal }));
    allColors.push({field: path, color: color})
  }
  console.log(allData)

  const [data, setData] = useState(dataStart);
  const [option, setOption] = useState(options);

  const handleSelectChange = event => {

    let dataset;
    let colorAndField;
    let color
    const dataUpdated = {
      labels,
      datasets: []
    };

    if (event.length > 0) {

      for (i = 0; i < event.length; i++) {
        dataset = {};
        colorAndField = allColors.find(x => x.field === event[i].label);
        color = colorAndField['color']
        
        dataset = {
          label: event[i].label,
          data: allData[event[i].value],
          borderColor: color,
          backgroundColor: color,
        }
        dataUpdated.datasets.push(dataset)
      }
    }

    setData(dataUpdated);
  };

  const colourStyles = {
    //container: (styles) => ({ ...styles, width: 300}),
    control: (styles) => ({ ...styles, backgroundColor: 'white' }),
    option: (styles) => ({ ...styles, color: 'black' }),
    multiValue: (styles) => ({ ...styles, backgroundColor: '#bcbcbc' }),
    multiValueRemove: (styles) => ({ ...styles, ':hover': {
      backgroundColor: 'gray',
      color: 'white',
    } })
  };

  return (
    <Container>

      <Select 
        closeMenuOnSelect={true}
        isMulti
        onChange={(handleSelectChange)} 
        options={optionsSelect} 
        styles={colourStyles}
      />
      <ButtonRefresh onClick={(e) => {setSelection(null)}}>
        <FaRedo />
      </ButtonRefresh>
      <ButtonZoom 
        onClick={(e) => {
          chartRef.current.resetZoom();
          options.plugins.zoom.zoom.mode = 'y';
          setOption(options);
        }}>
        Reset zoom
      </ButtonZoom>

      <ButtonZoom 
        onClick={(e) => {
          options.plugins.zoom.zoom.mode = 'xy';
          setOption(options)
        }}>
        Zoom xy
      </ButtonZoom>
      <ButtonZoom 
        onClick={(e) => {
          options.plugins.zoom.zoom.mode = 'x';
          setOption(options)
        }}>
        Zoom x
      </ButtonZoom>
      <ButtonZoom
        onClick={(e) => {
          options.plugins.zoom.zoom.mode = 'y';
          setOption(options)
        }}>
        Zoom y
      </ButtonZoom>
      <LineContainer>
        <Line ref={chartRef} options={option} data={data}
          onClick={(e) => {
        
            var activePoints = getElementAtEvent(chartRef.current,e);
            
            if (typeof activePoints[0] !== "undefined") {
              var index = activePoints[0]['index']
              //console.log(labels)
              const sampleId = labels[index];
              //const sam = fos.getSample(sampleId);
              setSelection(sampleId)
              //const clickedIndex = index;
              //const getIndex = (index: number) => {};
              //expandSample(sam, { index: clickedIndex, getIndex });
              //setSelection(null)
            }
          }
        } 
       />
      </LineContainer>
    </Container>
  )   

}

function getFieldsName() {
  const ds = useVal(fos.dataset)
  let i = 0;
  let fields = [];
  for (i = 0; i < ds['sampleFields'].length; i++) {
    if (ds['sampleFields'][i]['name'][0] != '_') // does not take into considerations fields that starts with '_' -> gives error
      fields.push(ds['sampleFields'][i]['name'])
  }
  return fields
}

function getSpecificField({field}) {
  const dataset = useVal(fos.dataset)
  const view = useVal(fos.view)
  const filters = useVal(fos.filters)
  const [aggregate, result, loading] = foa.useAggregation({view, filters, dataset})

  useEffect(() => {
    const aggregations = [
      new foa.aggregations.Values({fieldOrExpr: field})
    ]
    aggregate(aggregations, dataset.name)
  }, [dataset])
  
  if (loading) return '...' 

  return result[0]
}

export default Chart;
     
    /*
    <MultiSelect className="dark" value={selectedClient} onChange={(handleSelectChange)} options={optionsSelect} labelledBy="Select"/>

     <Select value={selectedClient} onChange={(handleSelectChange)} options={optionsSelect}/>
    <h1>
          <select id="fruits" value={fruit} 
              onChange={(e) => setFruit(e.target.value)}>
        <option value="apple">Apple</option>
        <option value="diametro_truth">Pear</option>
        <option value="Pineapple">Pineapple</option>
      </select>
      <h1>Selected Fruit: {fruit}</h1>
      <button onClick={(event) => { 
        setSelection([results[3]])
        const sampleId = results[3];
        //(next, sampleId, itemIndexMap) => {
        const clickedIndex = 0;

        const getIndex = (index: number) => {};

        expandSample(sam, { index: clickedIndex, getIndex });
            

      }}>cliccami</button>
      <button onClick={(e) => {
         setSelection(null)
      }}>Resetta</button>
     
   </h1> */

  /*console.log(results)
  console.log(Object.keys(results))
  console.log(Object.keys(results)[0])
  if (pippo===false)
  {
    let objid = Object.keys(results)[0]
    //setSelection([objid])
    pippo=true
  } */
  /*
  const createSourceData = (samples: {
    [key: string]: [string, number];
  }): GeoJSON.FeatureCollection<GeoJSON.Point, { id: string }> => {
    return {
      type: "FeatureCollection",
      features: Object.entries(samples).map(([id, coordinates]) => ({
        type: "Feature",
        properties: { id },
        geometry: { type: "Point", coordinates },
      })),
    };
  };*/
  //setSelection([results[0]])
  //setSelection(results[0])

  //console.log(data) 
  //console.log(results)
  //console.log(result[0][0])
  //let results = Count();
  //console.log(results[0])
  //let sample = fos.useSelectSample({sampleId:results[0]})
  //fos.useSetSelected()
  //console.log(sample)
  // select a dataset
  //let aaa = fos.useSetSelected();
  //console.log(aaa)

/*(
    <h1>
      <button onClick={(event) => { 
        
        setSelection(["63500f35586c546ccb479cd5"])
        //const sample = store.samples.get("63500f35586c546ccb479cd5");
        //expandSample(sample, { index: clickedIndex, getIndex });
        

        }}>cliccami</button>
    </h1>
  )*/


/*
function Count({field}) {
  const dataset = useVal(fos.dataset)
  const view = useVal(fos.view)
  const filters = useVal(fos.filters)
  const [aggregate, result, loading] = foa.useAggregation({view, filters, dataset})

  useEffect(() => {
    aggregate(
      [
        new foa.aggregations.Values({
          fieldOrExpr: "id",
        }),
        new foa.aggregations.Values({
          fieldOrExpr: 'diametro_truth',
        }),
      ],
      dataset.name
    );
  }, [dataset])
  
  let samples = React.useMemo(
    () =>
      result
        ? result[0].reduce((acc, id, i) => {
            if (result[1][i]) {
              acc[id] = result[1][i];
            }
            return acc;
          }, {})
        : {},
    [result]
  )
  
  if (loading) return '...' 

  return result[0]
}

function getId({field}) {
  const dataset = useVal(fos.dataset)
  const view = useVal(fos.view)
  const filters = useVal(fos.filters)
  const [aggregate, result, loading] = foa.useAggregation({view, filters, dataset})

  useEffect(() => {
    const aggregations = [
      new foa.aggregations.Values({fieldOrExpr: 'diametro_truth'})
    ]
    aggregate(aggregations, dataset.name)
  }, [dataset])
  
  if (loading) return '...' 

  return <strong>{result[0]}</strong>
}


*/