const colorList = [
  '#54639C',
  '#5F81D8',
  '#5889C4',
  '#5C539B',
  '#805A9C',
  '#D770A1',
  '#D8707A',
  '#2A908F',
  '#50A06A',
  '#7BBAA0',
  '#91C073',
  '#BBD273',
  '#F0E34F',
  '#ECB763',
  '#E39640',
  '#D9704C',
  '#D9534C',
  '#C64F58',
  '#3A4673',
  '#68798E',
  '#C5C8CC'
];

/**
 * 本体被删除时, 知识图谱详情中无法获取颜色
 * 如果没有颜色值, 生成随机颜色
 * @param {String} color 颜色值
 */
const getCorrectColor = color => {
  if (color) return color;

  const { length } = colorList;

  return colorList[parseInt(Math.random() * (length - 1))];
};

export default getCorrectColor;
