import { registerComponent, PluginComponentType } from '/home/musausr/fiftyone/fiftyone/app/packages/plugins'

import Chart from "./Chart";

export { default as Chart } from "./Chart";

//import Prova from "./Prova";

//export { default as Prova } from "./Prova";

registerComponent({
  name: 'Chart',
  label: 'Chart',
  component: Chart,
  type: PluginComponentType.Plot,
  activator: myActivator
})

function myActivator({dataset}) {
  // return dataset.name === 'quickstart'
  return true
}
