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
import Chart from "./Chart";

export { default as Chart } from "./Chart";
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


const Prova: React.FC<{}> = () => { 
  const [showB, setShowB] = useState(true);
  
  return (
    <Container>
        <ButtonRefresh onClick={(e) => {
        setShowB(false);
        delay(100).then(() => setShowB(true));
      }}>
        </ButtonRefresh>
        {showB && <Chart />}
    </Container>
    
  )   

}
function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
  }
export default Prova;
