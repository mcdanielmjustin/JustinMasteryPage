var fs = require('fs');
var file = process.argv[2] || 'data/brain_meshes/full_brain_hires.glb';
var buf = fs.readFileSync(file);
var jsonLen = buf.readUInt32LE(12);
var json = JSON.parse(buf.slice(20, 20 + jsonLen).toString());
var accessors = json.accessors || [];
var meshes = json.meshes || [];
var totalTris = 0;
meshes.forEach(function(m) {
  (m.primitives || []).forEach(function(p) {
    if (p.indices !== undefined) {
      var acc = accessors[p.indices];
      if (acc) totalTris += acc.count / 3;
    }
  });
});
var imgs = json.images || [];
console.log(file + ': ' + Math.round(totalTris).toLocaleString() + ' triangles, ' + imgs.length + ' embedded image(s)');
